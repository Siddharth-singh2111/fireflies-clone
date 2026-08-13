"""Idempotent database seeder.

Run with:  python -m app.seed
Drops and recreates all tables, then loads the default user and the curated
demo meetings so the app is immediately usable. Safe to re-run at any time.
"""
from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone

from app import models
from app.database import Base, SessionLocal, engine
from app.seed_data import DEFAULT_USER, MEETINGS
from app.services.meeting_service import _SPEAKER_COLORS
from app.services.transcript_parser import parse_transcript


def reset_schema() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed() -> None:
    reset_schema()
    db = SessionLocal()
    try:
        user = models.User(**DEFAULT_USER)
        db.add(user)
        db.flush()

        tag_cache: dict[str, models.Tag] = {}

        def get_tag(name: str) -> models.Tag:
            key = name.lower()
            if key not in tag_cache:
                tag = models.Tag(name=name)
                db.add(tag)
                db.flush()
                tag_cache[key] = tag
            return tag_cache[key]

        for spec in MEETINGS:
            parsed = parse_transcript(spec["transcript"], "text")

            meeting = models.Meeting(
                user_id=user.id,
                title=spec["title"],
                meeting_date=datetime.now(timezone.utc) - timedelta(days=spec["days_ago"]),
                duration_sec=parsed.duration_ms // 1000,
                audio_url=spec.get("audio_url"),
                status="completed",
            )
            db.add(meeting)

            for p in spec["participants"]:
                meeting.participants.append(
                    models.Participant(name=p["name"], email=p.get("email"))
                )
            for t in spec.get("tags", []):
                meeting.tags.append(get_tag(t))

            # Speakers + segments from the parsed transcript.
            colors = itertools.cycle(_SPEAKER_COLORS)
            speaker_by_label: dict[str, models.Speaker] = {}
            for label in parsed.speakers:
                sp = models.Speaker(label=label, display_name=label, color=next(colors))
                meeting.speakers.append(sp)
                speaker_by_label[label] = sp
            for seq, seg in enumerate(parsed.segments):
                meeting.segments.append(models.TranscriptSegment(
                    seq=seq, start_ms=seg.start_ms, end_ms=seg.end_ms, text=seg.text,
                    speaker=speaker_by_label.get(seg.speaker) if seg.speaker else None,
                ))

            # Curated summary / action items / topics.
            s = spec["summary"]
            meeting.summary = models.Summary(
                overview=s["overview"], keywords=s.get("keywords"),
                sentiment=s.get("sentiment"), generated_by="seed",
            )
            for a in spec["action_items"]:
                meeting.action_items.append(models.ActionItem(
                    text=a["text"], assignee=a.get("assignee"),
                    is_completed=a.get("done", False),
                ))
            for seq, t in enumerate(spec["topics"]):
                meeting.topics.append(models.Topic(
                    seq=seq, title=t["title"], start_ms=t["start_ms"],
                ))

        db.commit()
        count = db.query(models.Meeting).count()
        print(f"✓ Seeded {count} meetings for user '{user.name}' ({user.email}).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
