"""SQLAlchemy ORM models — the database schema.

Design decisions worth explaining in the interview:

* Timestamps inside a meeting are stored as integer milliseconds
  (`start_ms` / `end_ms`). Integers are exact, trivial to compare, and map
  directly onto an HTML media element's `currentTime` (seconds) — no timezone
  or float-rounding headaches when syncing the transcript to the player.

* The transcript is stored as one row per segment (a spoken line), not a single
  text blob. That is what makes per-line seeking, search-highlighting, and
  per-segment comments possible, and it keeps rows small.

* `Summary` is 1:1 with `Meeting`; action items, topics, segments, participants
  and speakers are 1:many. Every child has `ondelete="CASCADE"` + a cascading
  relationship, so deleting a meeting cleanly removes everything under it.

* A single default `User` stands in for auth, which the assignment says to mock.
  The FK is still modelled properly so real multi-user auth is a drop-in later.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    meetings: Mapped[list[Meeting]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    meeting_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )
    duration_sec: Mapped[int] = mapped_column(Integer, default=0)
    # Placeholder media (a sample file / public URL). Real STT is out of scope.
    audio_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    owner: Mapped[User] = relationship(back_populates="meetings")
    participants: Mapped[list[Participant]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    speakers: Mapped[list[Speaker]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    segments: Mapped[list[TranscriptSegment]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.seq",
    )
    summary: Mapped[Summary | None] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", uselist=False
    )
    action_items: Mapped[list[ActionItem]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    topics: Mapped[list[Topic]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="Topic.seq",
    )
    tags: Mapped[list[Tag]] = relationship(
        secondary="meeting_tags", back_populates="meetings"
    )


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))

    meeting: Mapped[Meeting] = relationship(back_populates="participants")


class Speaker(Base):
    """A speaker label local to one meeting, e.g. "Speaker 1" → "Priya Nair"."""

    __tablename__ = "speakers"
    __table_args__ = (UniqueConstraint("meeting_id", "label", name="uq_speaker_label"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(60), nullable=False)   # stable key
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    color: Mapped[str | None] = mapped_column(String(20))            # UI accent

    meeting: Mapped[Meeting] = relationship(back_populates="speakers")
    segments: Mapped[list[TranscriptSegment]] = relationship(back_populates="speaker")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    speaker_id: Mapped[int | None] = mapped_column(
        ForeignKey("speakers.id", ondelete="SET NULL")
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)   # 0-based order
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    meeting: Mapped[Meeting] = relationship(back_populates="segments")
    speaker: Mapped[Speaker | None] = relationship(back_populates="segments")
    comments: Mapped[list[Comment]] = relationship(
        back_populates="segment", cascade="all, delete-orphan"
    )


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), unique=True, index=True
    )
    overview: Mapped[str] = mapped_column(Text, default="")
    # Short bullet lines stored as newline-separated text to keep SQLite simple.
    keywords: Mapped[str | None] = mapped_column(Text)
    sentiment: Mapped[str | None] = mapped_column(String(30))
    generated_by: Mapped[str] = mapped_column(String(30), default="seed")  # seed|rule|llm
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    meeting: Mapped[Meeting] = relationship(back_populates="summary")


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    assignee: Mapped[str | None] = mapped_column(String(160))
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    meeting: Mapped[Meeting] = relationship(back_populates="action_items")


class Topic(Base):
    """A chapter / outline entry that points at a moment in the meeting."""

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, default=0)

    meeting: Mapped[Meeting] = relationship(back_populates="topics")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)

    meetings: Mapped[list[Meeting]] = relationship(
        secondary="meeting_tags", back_populates="tags"
    )


class MeetingTag(Base):
    __tablename__ = "meeting_tags"

    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class Comment(Base):
    """Bonus: a note/highlight attached to one transcript segment."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    segment_id: Mapped[int] = mapped_column(
        ForeignKey("transcript_segments.id", ondelete="CASCADE"), index=True
    )
    author: Mapped[str] = mapped_column(String(160), default="You")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    segment: Mapped[TranscriptSegment] = relationship(back_populates="comments")
