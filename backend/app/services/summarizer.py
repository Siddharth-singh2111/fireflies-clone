"""Deterministic, offline summary engine.

This is the fallback half of the "hybrid" AI approach: no network, no API key,
always produces something sensible. It powers uploaded meetings by default and
backs the LLM features whenever a key is not configured.

Techniques (all classic, explainable IR heuristics):
* Overview  — extractive: score sentences by summed frequency of their content
              words, take the top few in original order.
* Keywords  — most frequent content words.
* Actions   — sentences containing commitment/imperative cues, with a light
              "<Name> will ..." assignee extraction.
* Topics    — split the timeline into chapters, title each by its top keyword.
* Sentiment — lexicon tally → Positive / Neutral / Negative.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from app.services.transcript_parser import ParsedSegment

_STOPWORDS = set("""
a an and are as at be been but by for from had has have he her here his how i in
into is it its just like me my no not of on or our so than that the their them then
there these they this to too us was we were what when where which who will with you
your yeah okay ok um uh right sure gonna wanna kind lot really actually basically
""".split())

_ACTION_CUES = re.compile(
    r"\b(will|i'll|we'll|let's|need to|needs to|have to|has to|should|must|"
    r"action item|follow[- ]?up|to-?do|assign|send|share|schedule|set up|"
    r"prepare|review|draft|finalize|circle back|by (?:monday|tuesday|wednesday|"
    r"thursday|friday|next week|tomorrow|eod|end of))\b",
    re.IGNORECASE,
)
_ASSIGNEE_RE = re.compile(r"\b([A-Z][a-z]+)\s+(?:will|to|is going to|should|needs to|'ll)\b")

_POS = set("great good excellent happy agree love perfect awesome win success "
           "progress excited confident aligned strong nice thanks appreciate".split())
_NEG = set("bad blocker blocked issue problem concern risk worried delay fail "
           "difficult hard confused stuck disagree unfortunately behind".split())


@dataclass
class GeneratedSummary:
    overview: str
    keywords: list[str]
    sentiment: str
    action_items: list[dict] = field(default_factory=list)   # {text, assignee}
    topics: list[dict] = field(default_factory=list)         # {title, start_ms}
    generated_by: str = "rule"


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 2]


def _content_words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-zA-Z][a-zA-Z'-]+", text.lower())
            if w not in _STOPWORDS and len(w) > 2]


def _word_frequencies(segments: list[ParsedSegment]) -> Counter:
    freq: Counter = Counter()
    for seg in segments:
        freq.update(_content_words(seg.text))
    return freq


def _overview(segments: list[ParsedSegment], freq: Counter, max_sentences: int = 4) -> str:
    scored: list[tuple[float, int, str]] = []
    idx = 0
    for seg in segments:
        for sent in _sentences(seg.text):
            words = _content_words(sent)
            if not words:
                idx += 1
                continue
            score = sum(freq.get(w, 0) for w in words) / len(words)
            scored.append((score, idx, sent))
            idx += 1
    if not scored:
        return ""
    top = sorted(scored, key=lambda x: x[0], reverse=True)[:max_sentences]
    top.sort(key=lambda x: x[1])  # restore reading order
    return " ".join(s for _, _, s in top)


def _action_items(segments: list[ParsedSegment]) -> list[dict]:
    seen: set[str] = set()
    items: list[dict] = []
    for seg in segments:
        for sent in _sentences(seg.text):
            if not _ACTION_CUES.search(sent):
                continue
            key = sent.lower()
            if key in seen or len(sent) < 8:
                continue
            seen.add(key)
            m = _ASSIGNEE_RE.search(sent)
            assignee = m.group(1) if m else (seg.speaker or None)
            items.append({"text": sent.rstrip(".") + ".", "assignee": assignee})
            if len(items) >= 8:
                return items
    return items


def _topics(segments: list[ParsedSegment], chapters: int = 5) -> list[dict]:
    if not segments:
        return []
    chapters = max(1, min(chapters, len(segments)))
    size = max(1, len(segments) // chapters)
    topics: list[dict] = []
    for i in range(0, len(segments), size):
        chunk = segments[i:i + size]
        if not chunk:
            continue
        freq = Counter()
        for seg in chunk:
            freq.update(_content_words(seg.text))
        top = [w for w, _ in freq.most_common(3)]
        title = ", ".join(w.capitalize() for w in top) if top else "Discussion"
        topics.append({"title": title, "start_ms": chunk[0].start_ms})
        if len(topics) >= chapters:
            break
    return topics


def _sentiment(freq: Counter) -> str:
    pos = sum(freq.get(w, 0) for w in _POS)
    neg = sum(freq.get(w, 0) for w in _NEG)
    if pos > neg * 1.3:
        return "Positive"
    if neg > pos * 1.3:
        return "Negative"
    return "Neutral"


def generate_summary(segments: list[ParsedSegment]) -> GeneratedSummary:
    if not segments:
        return GeneratedSummary(
            overview="No transcript content was available to summarize.",
            keywords=[], sentiment="Neutral",
        )
    freq = _word_frequencies(segments)
    keywords = [w for w, _ in freq.most_common(8)]
    return GeneratedSummary(
        overview=_overview(segments, freq),
        keywords=keywords,
        sentiment=_sentiment(freq),
        action_items=_action_items(segments),
        topics=_topics(segments),
    )
