"""Optional LLM layer with a guaranteed offline fallback.

The assignment's "hybrid" choice: if an API key is configured we call a real LLM
for richer summaries and Q&A; if not, we degrade gracefully to deterministic
logic so a live demo can never fail on a missing key or a network blip.

`httpx` is called directly (no heavyweight SDK) to keep the dependency surface
small and the behaviour easy to explain.
"""
from __future__ import annotations

import re
from collections import Counter

import httpx

from app.config import get_settings
from app.services.summarizer import _STOPWORDS, _content_words
from app.services.transcript_parser import ParsedSegment

settings = get_settings()


def _transcript_text(segments: list[ParsedSegment], limit_chars: int = 12000) -> str:
    lines = []
    for s in segments:
        who = s.speaker or "Speaker"
        lines.append(f"{who}: {s.text}")
    text = "\n".join(lines)
    return text[:limit_chars]


# --------------------------------------------------------------------------- #
# Provider calls (best-effort; any failure raises and callers fall back)
# --------------------------------------------------------------------------- #
def _call_anthropic(system: str, user: str) -> str:
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings.llm_model,
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return "".join(block.get("text", "") for block in data.get("content", [])).strip()


def _call_openai(system: str, user: str) -> str:
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json={
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": 1024,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _call_llm(system: str, user: str) -> str:
    if settings.llm_provider == "anthropic":
        return _call_anthropic(system, user)
    if settings.llm_provider == "openai":
        return _call_openai(system, user)
    raise RuntimeError("No LLM provider configured")


# --------------------------------------------------------------------------- #
# Retrieval for the "ask this meeting" fallback
# --------------------------------------------------------------------------- #
def retrieve_relevant(segments: list[ParsedSegment], question: str, k: int = 4) -> list[ParsedSegment]:
    """Rank segments by overlap with the question's content words (bag-of-words)."""
    q_words = Counter(w for w in _content_words(question))
    if not q_words:
        return segments[:k]
    scored = []
    for seg in segments:
        words = _content_words(seg.text)
        if not words:
            continue
        overlap = sum(q_words[w] for w in words if w in q_words)
        if overlap:
            scored.append((overlap / (len(words) ** 0.5), seg))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:k]]


def answer_question(segments: list[ParsedSegment], question: str) -> tuple[str, list[ParsedSegment], str]:
    """Return (answer, source_segments, generated_by)."""
    relevant = retrieve_relevant(segments, question, k=4)

    if settings.llm_enabled:
        try:
            context = "\n".join(
                f"[{s.start_ms}] {s.speaker or 'Speaker'}: {s.text}" for s in relevant
            )
            system = (
                "You are a meeting assistant. Answer the user's question using ONLY the "
                "provided transcript excerpts. Be concise. If the excerpts don't contain "
                "the answer, say so plainly."
            )
            user = f"Transcript excerpts:\n{context}\n\nQuestion: {question}"
            answer = _call_llm(system, user)
            if answer:
                return answer, relevant, "llm"
        except Exception:
            pass  # fall through to extractive

    # Extractive fallback: stitch the most relevant lines into a grounded answer.
    if not relevant:
        return (
            "I couldn't find anything about that in this meeting's transcript.",
            [], "extractive",
        )
    joined = " ".join(s.text for s in relevant)
    answer = (
        "Based on the transcript, here's what was said: "
        + (joined[:500] + ("…" if len(joined) > 500 else ""))
    )
    return answer, relevant, "extractive"


def regenerate_overview(segments: list[ParsedSegment], fallback_overview: str) -> tuple[str, str]:
    """Return (overview_text, generated_by). Uses LLM if available, else the rule text."""
    if settings.llm_enabled:
        try:
            system = (
                "You summarize meeting transcripts into a crisp 3-4 sentence overview "
                "capturing decisions and outcomes. Return prose only, no preamble."
            )
            overview = _call_llm(system, _transcript_text(segments))
            if overview:
                return overview, "llm"
        except Exception:
            pass
    return fallback_overview, "rule"
