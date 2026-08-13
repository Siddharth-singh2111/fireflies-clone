"""'Ask a question about this meeting' (bonus).

Retrieves the most relevant transcript segments and answers grounded in them,
via the LLM if a key is configured, otherwise via the extractive fallback.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user
from app.services.llm import answer_question
from app.services.transcript_parser import ParsedSegment

router = APIRouter(prefix="/api/meetings/{meeting_id}/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatResponse)
def ask_meeting(
    meeting_id: int,
    payload: schemas.ChatRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    m = (
        db.query(models.Meeting)
        .options(
            selectinload(models.Meeting.segments).selectinload(models.TranscriptSegment.speaker)
        )
        .filter(models.Meeting.id == meeting_id, models.Meeting.user_id == user.id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Keep a parallel list so we can map fallback ParsedSegments back to real IDs.
    id_by_key: dict[tuple[int, str], models.TranscriptSegment] = {}
    parsed: list[ParsedSegment] = []
    for seg in m.segments:
        ps = ParsedSegment(
            speaker=seg.speaker.display_name if seg.speaker else None,
            start_ms=seg.start_ms, end_ms=seg.end_ms, text=seg.text,
        )
        parsed.append(ps)
        id_by_key[(seg.start_ms, seg.text)] = seg

    answer, sources, generated_by = answer_question(parsed, payload.question)

    source_out = []
    for s in sources:
        seg = id_by_key.get((s.start_ms, s.text))
        if seg:
            source_out.append(schemas.ChatSource(
                segment_id=seg.id, start_ms=seg.start_ms, text=seg.text,
                speaker=seg.speaker.display_name if seg.speaker else None,
            ))
    return schemas.ChatResponse(answer=answer, sources=source_out, generated_by=generated_by)
