"""Parse an uploaded/pasted transcript into normalized segments.

Three input shapes are supported and auto-detected:

1. JSON   — a list of {speaker, start, end, text} objects (start/end may be
            seconds, ms, or "HH:MM:SS" strings). Also accepts Fireflies-style
            {"sentences": [...]}.
2. WebVTT — standard .vtt cue blocks, with an optional "Name: text" payload.
3. Text   — lines like "Priya: hello", "[00:01:05] Priya: hello", or
            "Priya (1:05): hello". Timestamps are optional.

When timestamps are missing we synthesize them from word counts at ~150 wpm so
the transcript still drives the media player. The output is provider-agnostic:
a list of ParsedSegment plus the ordered set of distinct speaker labels.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

WORDS_PER_MINUTE = 150
_MIN_SEGMENT_MS = 1200


@dataclass
class ParsedSegment:
    speaker: str | None
    start_ms: int
    end_ms: int
    text: str


@dataclass
class ParsedTranscript:
    segments: list[ParsedSegment]
    speakers: list[str]        # distinct, in first-seen order
    duration_ms: int


# --------------------------------------------------------------------------- #
# Timestamp helpers
# --------------------------------------------------------------------------- #
def _ts_to_ms(value: object) -> int | None:
    """Coerce seconds/ms numbers or "HH:MM:SS(.mmm)" strings into milliseconds."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Heuristic: treat large numbers as already-ms, small as seconds.
        return int(value) if value > 10_000 else int(value * 1000)
    if isinstance(value, str):
        s = value.strip().replace(",", ".")
        if not s:
            return None
        parts = s.split(":")
        try:
            if len(parts) == 3:
                h, m, sec = parts
                return int((int(h) * 3600 + int(m) * 60 + float(sec)) * 1000)
            if len(parts) == 2:
                m, sec = parts
                return int((int(m) * 60 + float(sec)) * 1000)
            return int(float(s) * 1000)
        except ValueError:
            return None
    return None


def _estimate_ms(text: str) -> int:
    words = max(1, len(text.split()))
    return max(_MIN_SEGMENT_MS, int(words / WORDS_PER_MINUTE * 60_000))


def _fill_timestamps(segments: list[ParsedSegment]) -> None:
    """Ensure every segment has monotonic start/end, synthesizing when needed."""
    cursor = 0
    for seg in segments:
        if seg.start_ms is None or seg.start_ms < cursor:
            seg.start_ms = cursor
        if seg.end_ms is None or seg.end_ms <= seg.start_ms:
            seg.end_ms = seg.start_ms + _estimate_ms(seg.text)
        cursor = seg.end_ms


# --------------------------------------------------------------------------- #
# Format-specific parsers
# --------------------------------------------------------------------------- #
def _looks_like_json(raw: str) -> bool:
    try:
        json.loads(raw)
        return True
    except (ValueError, json.JSONDecodeError):
        return False


def _parse_json(raw: str) -> list[ParsedSegment]:
    data = json.loads(raw)
    if isinstance(data, dict):
        data = data.get("segments") or data.get("sentences") or data.get("transcript") or []
    if not isinstance(data, list):
        raise ValueError("JSON transcript must be a list or contain a segments/sentences list")

    out: list[ParsedSegment] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        text = (item.get("text") or item.get("sentence") or "").strip()
        if not text:
            continue
        speaker = item.get("speaker") or item.get("speaker_name") or item.get("name")
        start = _ts_to_ms(item.get("start", item.get("start_time", item.get("startTime"))))
        end = _ts_to_ms(item.get("end", item.get("end_time", item.get("endTime"))))
        out.append(ParsedSegment(
            speaker=str(speaker).strip() if speaker else None,
            start_ms=start, end_ms=end, text=text,
        ))
    return out


_VTT_SPEAKER_RE = re.compile(r"^\s*(?:<v\s+([^>]+)>|([A-Za-z0-9 ._-]{1,40}):)\s*(.*)$")


def _parse_vtt(raw: str) -> list[ParsedSegment]:
    out: list[ParsedSegment] = []
    blocks = re.split(r"\n\s*\n", raw.strip())
    time_re = re.compile(
        r"(\d{1,2}:\d{2}(?::\d{2})?[.,]?\d*)\s*-->\s*(\d{1,2}:\d{2}(?::\d{2})?[.,]?\d*)"
    )
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines or lines[0].strip().upper() == "WEBVTT":
            continue
        start = end = None
        text_lines: list[str] = []
        for ln in lines:
            m = time_re.search(ln)
            if m and start is None:
                start, end = _ts_to_ms(m.group(1)), _ts_to_ms(m.group(2))
            elif "-->" not in ln and not ln.strip().isdigit():
                text_lines.append(ln.strip())
        if not text_lines:
            continue
        payload = " ".join(text_lines)
        speaker = None
        sm = _VTT_SPEAKER_RE.match(payload)
        if sm:
            speaker = (sm.group(1) or sm.group(2) or "").strip() or None
            payload = sm.group(3).strip() or payload
        out.append(ParsedSegment(speaker=speaker, start_ms=start, end_ms=end, text=payload))
    return out


# "[00:01:05] Priya: text"  |  "Priya (1:05): text"  |  "Priya: text"
_LEAD_TS_RE = re.compile(r"^\s*[\[(]?\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*[\])]?\s*")
_SPEAKER_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9 ._'-]{0,39})\s*(?:\((\d{1,2}:\d{2}(?::\d{2})?)\))?\s*:\s*(.*)$")


def _parse_text(raw: str) -> list[ParsedSegment]:
    out: list[ParsedSegment] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        rest = line
        lead_ts = None
        lead = _LEAD_TS_RE.match(rest)
        if lead:
            lead_ts = _ts_to_ms(lead.group(1))
            rest = rest[lead.end():]

        sm = _SPEAKER_RE.match(rest)
        if sm:
            speaker = sm.group(1).strip()
            inline_ts = _ts_to_ms(sm.group(2)) if sm.group(2) else None
            text = sm.group(3).strip()
            if not text:
                continue
            out.append(ParsedSegment(
                speaker=speaker,
                start_ms=lead_ts if lead_ts is not None else inline_ts,
                end_ms=None, text=text,
            ))
        else:
            # Continuation / speaker-less line: append to previous or start fresh.
            text = rest.strip()
            if not text:
                continue
            if out:
                out[-1].text += " " + text
            else:
                out.append(ParsedSegment(speaker=None, start_ms=lead_ts, end_ms=None, text=text))
    return out


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def parse_transcript(raw: str, fmt: str | None = "auto") -> ParsedTranscript:
    raw = (raw or "").strip()
    if not raw:
        return ParsedTranscript(segments=[], speakers=[], duration_ms=0)

    fmt = (fmt or "auto").lower()
    if fmt == "auto":
        # Only treat as JSON if it genuinely parses as a JSON list/object.
        # (A plain-text line can start with "[" too, e.g. "[00:00:01] Alice:".)
        if raw[0] in "[{" and _looks_like_json(raw):
            fmt = "json"
        elif raw.upper().startswith("WEBVTT") or "-->" in raw[:200]:
            fmt = "vtt"
        else:
            fmt = "text"

    if fmt == "json":
        segments = _parse_json(raw)
    elif fmt == "vtt":
        segments = _parse_vtt(raw)
    else:
        segments = _parse_text(raw)

    # Drop empties, fill timestamps, collect speakers.
    segments = [s for s in segments if s.text.strip()]
    _fill_timestamps(segments)

    speakers: list[str] = []
    for s in segments:
        if s.speaker and s.speaker not in speakers:
            speakers.append(s.speaker)

    duration_ms = segments[-1].end_ms if segments else 0
    return ParsedTranscript(segments=segments, speakers=speakers, duration_ms=duration_ms)
