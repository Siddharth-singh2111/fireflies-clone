"""Global search across every meeting's transcript (bonus)."""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/api/search", tags=["search"])


def _snippet(text: str, term: str, width: int = 60) -> str:
    idx = text.lower().find(term.lower())
    if idx == -1:
        return text[: width * 2] + ("…" if len(text) > width * 2 else "")
    start = max(0, idx - width)
    end = min(len(text), idx + len(term) + width)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"


@router.get("", response_model=schemas.GlobalSearchOut)
def global_search(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    q: str = Query(..., min_length=2, description="Search across all transcripts"),
    limit: int = Query(30, ge=1, le=100),
):
    like = f"%{q}%"
    rows = (
        db.query(models.TranscriptSegment)
        .options(joinedload(models.TranscriptSegment.speaker))
        .join(models.Meeting, models.TranscriptSegment.meeting_id == models.Meeting.id)
        .filter(models.Meeting.user_id == user.id)
        .filter(models.TranscriptSegment.text.ilike(like))
        .order_by(models.TranscriptSegment.meeting_id, models.TranscriptSegment.seq)
        .limit(limit)
        .all()
    )

    # Fetch titles in one pass to avoid N+1.
    meeting_ids = {r.meeting_id for r in rows}
    titles = dict(
        db.query(models.Meeting.id, models.Meeting.title)
        .filter(models.Meeting.id.in_(meeting_ids))
        .all()
    ) if meeting_ids else {}

    hits = [
        schemas.SearchHit(
            meeting_id=r.meeting_id,
            meeting_title=titles.get(r.meeting_id, ""),
            segment_id=r.id,
            start_ms=r.start_ms,
            snippet=_snippet(r.text, q),
            speaker=r.speaker.display_name if r.speaker else None,
        )
        for r in rows
    ]
    return schemas.GlobalSearchOut(query=q, hits=hits, total=len(hits))
