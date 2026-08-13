"""Transcript-segment sub-resources: speaker rename + comments (bonus)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/api", tags=["transcript"])


def _owned_meeting(db: Session, meeting_id: int, user_id: int) -> models.Meeting:
    m = (
        db.query(models.Meeting)
        .filter(models.Meeting.id == meeting_id, models.Meeting.user_id == user_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return m


# --- Rename a speaker across the whole meeting ---
@router.patch("/meetings/{meeting_id}/speakers/{speaker_id}", response_model=schemas.SpeakerOut)
def rename_speaker(
    meeting_id: int,
    speaker_id: int,
    payload: schemas.SpeakerRename,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _owned_meeting(db, meeting_id, user.id)
    speaker = (
        db.query(models.Speaker)
        .filter(models.Speaker.id == speaker_id, models.Speaker.meeting_id == meeting_id)
        .first()
    )
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    speaker.display_name = payload.display_name
    db.commit()
    db.refresh(speaker)
    return speaker


# --- Comments on a segment (bonus) ---
def _owned_segment(db: Session, meeting_id: int, segment_id: int, user_id: int) -> models.TranscriptSegment:
    _owned_meeting(db, meeting_id, user_id)
    seg = (
        db.query(models.TranscriptSegment)
        .filter(
            models.TranscriptSegment.id == segment_id,
            models.TranscriptSegment.meeting_id == meeting_id,
        )
        .first()
    )
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")
    return seg


@router.get("/meetings/{meeting_id}/segments/{segment_id}/comments",
            response_model=list[schemas.CommentOut])
def list_comments(
    meeting_id: int,
    segment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    seg = _owned_segment(db, meeting_id, segment_id, user.id)
    return seg.comments


@router.post("/meetings/{meeting_id}/segments/{segment_id}/comments",
             response_model=schemas.CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    meeting_id: int,
    segment_id: int,
    payload: schemas.CommentIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _owned_segment(db, meeting_id, segment_id, user.id)
    comment = models.Comment(
        segment_id=segment_id, author=payload.author or "You", body=payload.body,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/meetings/{meeting_id}/segments/{segment_id}/comments/{comment_id}",
               status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    meeting_id: int,
    segment_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _owned_segment(db, meeting_id, segment_id, user.id)
    comment = (
        db.query(models.Comment)
        .filter(models.Comment.id == comment_id, models.Comment.segment_id == segment_id)
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    db.delete(comment)
    db.commit()
