"""Pydantic v2 schemas — the typed boundary between HTTP and the ORM.

Every request body is validated here before it ever reaches the database, and
every response is serialized from an ORM object via `from_attributes=True`.
This is our first line of defence: no unvalidated input touches SQLAlchemy.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- User ----------
class UserOut(ORMModel):
    id: int
    name: str
    email: str
    avatar_url: str | None = None


# ---------- Participant ----------
class ParticipantIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: str | None = None


class ParticipantOut(ORMModel):
    id: int
    name: str
    email: str | None = None


# ---------- Speaker ----------
class SpeakerOut(ORMModel):
    id: int
    label: str
    display_name: str
    color: str | None = None


class SpeakerRename(BaseModel):
    display_name: str = Field(min_length=1, max_length=160)


# ---------- Transcript ----------
class SegmentOut(ORMModel):
    id: int
    seq: int
    start_ms: int
    end_ms: int
    text: str
    speaker_id: int | None = None


# ---------- Summary ----------
class SummaryOut(ORMModel):
    id: int
    overview: str
    keywords: str | None = None
    sentiment: str | None = None
    generated_by: str


class SummaryUpdate(BaseModel):
    overview: str | None = None
    keywords: str | None = None
    sentiment: str | None = None


# ---------- Action items ----------
class ActionItemIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    assignee: str | None = Field(default=None, max_length=160)
    due_date: datetime | None = None


class ActionItemUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=2000)
    assignee: str | None = None
    is_completed: bool | None = None
    due_date: datetime | None = None


class ActionItemOut(ORMModel):
    id: int
    text: str
    assignee: str | None = None
    is_completed: bool
    due_date: datetime | None = None


# ---------- Topics ----------
class TopicOut(ORMModel):
    id: int
    seq: int
    title: str
    start_ms: int


# ---------- Tags ----------
class TagOut(ORMModel):
    id: int
    name: str


# ---------- Comments ----------
class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    author: str | None = Field(default="You", max_length=160)


class CommentOut(ORMModel):
    id: int
    segment_id: int
    author: str
    body: str
    created_at: datetime


# ---------- Meetings ----------
class MeetingCreate(BaseModel):
    """Create a meeting via a form and/or a pasted transcript.

    `transcript_text` (when given) is parsed into speakers + segments. Supported
    formats are auto-detected: plain "Speaker: text" lines, WebVTT, or JSON.
    """
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    meeting_date: datetime | None = None
    duration_sec: int | None = Field(default=None, ge=0)
    audio_url: str | None = None
    participants: list[ParticipantIn] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    transcript_text: str | None = None
    transcript_format: str | None = None  # "auto" | "text" | "vtt" | "json"
    generate_summary: bool = True


class MeetingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    meeting_date: datetime | None = None
    duration_sec: int | None = Field(default=None, ge=0)
    audio_url: str | None = None
    participants: list[ParticipantIn] | None = None
    tags: list[str] | None = None


class MeetingListItem(ORMModel):
    """Lightweight row for the library/dashboard grid."""
    id: int
    title: str
    meeting_date: datetime
    duration_sec: int
    status: str
    participants: list[ParticipantOut] = []
    tags: list[TagOut] = []
    action_item_count: int = 0
    segment_count: int = 0


class MeetingDetail(ORMModel):
    id: int
    title: str
    description: str | None = None
    meeting_date: datetime
    duration_sec: int
    audio_url: str | None = None
    status: str
    participants: list[ParticipantOut] = []
    speakers: list[SpeakerOut] = []
    segments: list[SegmentOut] = []
    summary: SummaryOut | None = None
    action_items: list[ActionItemOut] = []
    topics: list[TopicOut] = []
    tags: list[TagOut] = []


class PaginatedMeetings(BaseModel):
    items: list[MeetingListItem]
    total: int
    page: int
    page_size: int


# ---------- Search ----------
class SearchHit(BaseModel):
    meeting_id: int
    meeting_title: str
    segment_id: int
    start_ms: int
    snippet: str
    speaker: str | None = None


class GlobalSearchOut(BaseModel):
    query: str
    hits: list[SearchHit]
    total: int


# ---------- Chat (ask this meeting) ----------
class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class ChatSource(BaseModel):
    segment_id: int
    start_ms: int
    text: str
    speaker: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource] = []
    generated_by: str  # "llm" | "extractive"
