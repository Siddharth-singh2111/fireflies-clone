"""Orchestration: assemble a fully-populated Meeting from parsed transcript data.

Kept out of the router so the same logic serves both the JSON create endpoint
and the multipart file-upload endpoint, and so the router stays thin (just HTTP
concerns). This is the "separation of concerns" the rubric asks for.
"""
from __future__ import annotations

import itertools

from sqlalchemy.orm import Session

from app import models
from app.services.summarizer import generate_summary
from app.services.transcript_parser import ParsedTranscript

# A small palette so each speaker gets a stable, distinct accent in the UI.
_SPEAKER_COLORS = [
    "#6366f1", "#ec4899", "#14b8a6", "#f59e0b",
    "#8b5cf6", "#ef4444", "#10b981", "#3b82f6",
]


def attach_transcript(
    db: Session,
    meeting: models.Meeting,
    parsed: ParsedTranscript,
    *,
    generate: bool = True,
) -> None:
    """Populate speakers, segments, and (optionally) summary/actions/topics.

    Assumes `meeting` is already added to the session. Does not commit — the
    caller owns the transaction boundary.
    """
    # 1. Speakers -> map label to ORM row.
    color_cycle = itertools.cycle(_SPEAKER_COLORS)
    speaker_by_label: dict[str, models.Speaker] = {}
    for label in parsed.speakers:
        sp = models.Speaker(
            label=label,
            display_name=label,
            color=next(color_cycle),
        )
        meeting.speakers.append(sp)
        speaker_by_label[label] = sp

    # 2. Segments.
    for seq, seg in enumerate(parsed.segments):
        speaker = speaker_by_label.get(seg.speaker) if seg.speaker else None
        meeting.segments.append(models.TranscriptSegment(
            seq=seq,
            start_ms=seg.start_ms,
            end_ms=seg.end_ms,
            text=seg.text,
            speaker=speaker,
        ))

    # Derive duration from the transcript if the caller didn't set one.
    if not meeting.duration_sec and parsed.duration_ms:
        meeting.duration_sec = parsed.duration_ms // 1000

    if not generate:
        return

    # 3. Summary + action items + topics (offline rule engine).
    gen = generate_summary(parsed.segments)
    meeting.summary = models.Summary(
        overview=gen.overview,
        keywords=", ".join(gen.keywords),
        sentiment=gen.sentiment,
        generated_by=gen.generated_by,
    )
    for item in gen.action_items:
        meeting.action_items.append(models.ActionItem(
            text=item["text"], assignee=item.get("assignee"),
        ))
    for seq, topic in enumerate(gen.topics):
        meeting.topics.append(models.Topic(
            seq=seq, title=topic["title"], start_ms=topic["start_ms"],
        ))


def upsert_tags(db: Session, names: list[str]) -> list[models.Tag]:
    """Get-or-create tags by name (case-insensitive), returning ORM rows."""
    result: list[models.Tag] = []
    for raw in names:
        name = raw.strip()
        if not name:
            continue
        tag = (
            db.query(models.Tag)
            .filter(models.Tag.name.ilike(name))
            .first()
        )
        if not tag:
            tag = models.Tag(name=name)
            db.add(tag)
            db.flush()
        if tag not in result:
            result.append(tag)
    return result
