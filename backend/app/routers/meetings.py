"""Meetings: list/search/filter/sort, CRUD, transcript upload, summary regen."""
from __future__ import annotations

import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user
from app.services import meeting_service
from app.services.llm import regenerate_overview
from app.services.transcript_parser import parse_transcript

router = APIRouter(prefix="/api/meetings", tags=["meetings"])
settings = get_settings()

_ALLOWED_EXT = {".txt", ".vtt", ".json"}


# --------------------------------------------------------------------------- #
# Serialization helpers
# --------------------------------------------------------------------------- #
def _to_list_item(m: models.Meeting) -> schemas.MeetingListItem:
    return schemas.MeetingListItem(
        id=m.id,
        title=m.title,
        meeting_date=m.meeting_date,
        duration_sec=m.duration_sec,
        status=m.status,
        participants=[schemas.ParticipantOut.model_validate(p) for p in m.participants],
        tags=[schemas.TagOut.model_validate(t) for t in m.tags],
        action_item_count=len(m.action_items),
        segment_count=len(m.segments),
    )


def _load_full(db: Session, meeting_id: int, user_id: int) -> models.Meeting:
    m = (
        db.query(models.Meeting)
        .options(
            selectinload(models.Meeting.participants),
            selectinload(models.Meeting.speakers),
            selectinload(models.Meeting.segments),
            selectinload(models.Meeting.action_items),
            selectinload(models.Meeting.topics),
            selectinload(models.Meeting.tags),
            selectinload(models.Meeting.summary),
        )
        .filter(models.Meeting.id == meeting_id, models.Meeting.user_id == user_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return m


# --------------------------------------------------------------------------- #
# List (search + filter + sort + paginate)
# --------------------------------------------------------------------------- #
@router.get("", response_model=schemas.PaginatedMeetings)
def list_meetings(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    q: str | None = Query(None, description="Search title/description/participant"),
    participant: str | None = Query(None),
    tag: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    sort: str = Query("recent", pattern="^(recent|oldest|title|duration)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
):
    query = db.query(models.Meeting).filter(models.Meeting.user_id == user.id)

    if q:
        like = f"%{q}%"
        query = query.outerjoin(models.Meeting.participants).filter(
            or_(
                models.Meeting.title.ilike(like),
                models.Meeting.description.ilike(like),
                models.Participant.name.ilike(like),
            )
        ).distinct()

    if participant:
        query = query.join(models.Meeting.participants).filter(
            models.Participant.name.ilike(f"%{participant}%")
        ).distinct()

    if tag:
        query = query.join(models.Meeting.tags).filter(models.Tag.name.ilike(tag)).distinct()

    if date_from:
        query = query.filter(models.Meeting.meeting_date >= date_from)
    if date_to:
        query = query.filter(models.Meeting.meeting_date <= date_to)

    sort_map = {
        "recent": models.Meeting.meeting_date.desc(),
        "oldest": models.Meeting.meeting_date.asc(),
        "title": models.Meeting.title.asc(),
        "duration": models.Meeting.duration_sec.desc(),
    }
    query = query.order_by(sort_map[sort])

    total = query.with_entities(func.count(func.distinct(models.Meeting.id))).scalar() or 0

    meetings = (
        query.options(
            selectinload(models.Meeting.participants),
            selectinload(models.Meeting.tags),
            selectinload(models.Meeting.action_items),
            selectinload(models.Meeting.segments),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return schemas.PaginatedMeetings(
        items=[_to_list_item(m) for m in meetings],
        total=total, page=page, page_size=page_size,
    )


# --------------------------------------------------------------------------- #
# Create (form + optional pasted transcript)
# --------------------------------------------------------------------------- #
@router.post("", response_model=schemas.MeetingDetail, status_code=status.HTTP_201_CREATED)
def create_meeting(
    payload: schemas.MeetingCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    meeting = models.Meeting(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        duration_sec=payload.duration_sec or 0,
        audio_url=payload.audio_url,
    )
    if payload.meeting_date:
        meeting.meeting_date = payload.meeting_date

    for p in payload.participants:
        meeting.participants.append(models.Participant(name=p.name, email=p.email))

    db.add(meeting)
    meeting.tags = meeting_service.upsert_tags(db, payload.tags)

    if payload.transcript_text:
        parsed = parse_transcript(payload.transcript_text, payload.transcript_format or "auto")
        meeting_service.attach_transcript(db, meeting, parsed, generate=payload.generate_summary)

    db.commit()
    return _load_full(db, meeting.id, user.id)


# --------------------------------------------------------------------------- #
# Upload a transcript file (.txt/.vtt/.json)
# --------------------------------------------------------------------------- #
@router.post("/upload", response_model=schemas.MeetingDetail, status_code=status.HTTP_201_CREATED)
async def upload_meeting(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(None),
    participants: str | None = Form(None, description="JSON array of {name,email}"),
    tags: str | None = Form(None, description="Comma-separated tag names"),
):
    # --- validate the upload before touching it ---
    name = (file.filename or "").lower()
    ext = name[name.rfind("."):] if "." in name else ""
    if ext not in _ALLOWED_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(_ALLOWED_EXT))}",
        )
    raw = await file.read()
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_bytes // (1024 * 1024)} MB limit",
        )
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text")

    fmt = {".vtt": "vtt", ".json": "json", ".txt": "text"}[ext]

    meeting = models.Meeting(user_id=user.id, title=title.strip(), description=description)
    if participants:
        try:
            for p in json.loads(participants):
                meeting.participants.append(
                    models.Participant(name=p["name"], email=p.get("email"))
                )
        except (json.JSONDecodeError, KeyError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid participants JSON")
    db.add(meeting)

    if tags:
        meeting.tags = meeting_service.upsert_tags(db, tags.split(","))

    parsed = parse_transcript(content, fmt)
    if not parsed.segments:
        raise HTTPException(status_code=400, detail="No transcript segments could be parsed from the file")
    meeting_service.attach_transcript(db, meeting, parsed, generate=True)

    db.commit()
    return _load_full(db, meeting.id, user.id)


# --------------------------------------------------------------------------- #
# Read one
# --------------------------------------------------------------------------- #
@router.get("/{meeting_id}", response_model=schemas.MeetingDetail)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return _load_full(db, meeting_id, user.id)


# --------------------------------------------------------------------------- #
# Update metadata
# --------------------------------------------------------------------------- #
@router.patch("/{meeting_id}", response_model=schemas.MeetingDetail)
def update_meeting(
    meeting_id: int,
    payload: schemas.MeetingUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    m = _load_full(db, meeting_id, user.id)
    data = payload.model_dump(exclude_unset=True)

    for field in ("title", "description", "meeting_date", "duration_sec", "audio_url"):
        if field in data:
            setattr(m, field, data[field])

    if "participants" in data and data["participants"] is not None:
        m.participants.clear()
        for p in payload.participants:
            m.participants.append(models.Participant(name=p.name, email=p.email))

    if "tags" in data and data["tags"] is not None:
        m.tags = meeting_service.upsert_tags(db, payload.tags)

    db.commit()
    return _load_full(db, meeting_id, user.id)


# --------------------------------------------------------------------------- #
# Delete (cascades to all children)
# --------------------------------------------------------------------------- #
@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    m = (
        db.query(models.Meeting)
        .filter(models.Meeting.id == meeting_id, models.Meeting.user_id == user.id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    db.delete(m)
    db.commit()


# --------------------------------------------------------------------------- #
# Regenerate summary (LLM if configured, else rule engine)
# --------------------------------------------------------------------------- #
@router.post("/{meeting_id}/regenerate-summary", response_model=schemas.SummaryOut)
def regenerate_summary(
    meeting_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    from app.services.summarizer import generate_summary
    from app.services.transcript_parser import ParsedSegment

    m = _load_full(db, meeting_id, user.id)
    parsed_segments = [
        ParsedSegment(
            speaker=(seg.speaker.display_name if seg.speaker else None),
            start_ms=seg.start_ms, end_ms=seg.end_ms, text=seg.text,
        )
        for seg in m.segments
    ]
    gen = generate_summary(parsed_segments)
    overview, generated_by = regenerate_overview(parsed_segments, gen.overview)

    if not m.summary:
        m.summary = models.Summary(meeting_id=m.id)
    m.summary.overview = overview
    m.summary.keywords = ", ".join(gen.keywords)
    m.summary.sentiment = gen.sentiment
    m.summary.generated_by = generated_by
    db.commit()
    db.refresh(m.summary)
    return schemas.SummaryOut.model_validate(m.summary)
