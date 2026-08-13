"""CRUD for a meeting's action items (add / edit / complete / delete)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/api/meetings/{meeting_id}/action-items", tags=["action-items"])


def _owned_meeting(db: Session, meeting_id: int, user_id: int) -> models.Meeting:
    m = (
        db.query(models.Meeting)
        .filter(models.Meeting.id == meeting_id, models.Meeting.user_id == user_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return m


def _owned_item(db: Session, meeting_id: int, item_id: int, user_id: int) -> models.ActionItem:
    _owned_meeting(db, meeting_id, user_id)
    item = (
        db.query(models.ActionItem)
        .filter(models.ActionItem.id == item_id, models.ActionItem.meeting_id == meeting_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return item


@router.post("", response_model=schemas.ActionItemOut, status_code=status.HTTP_201_CREATED)
def create_action_item(
    meeting_id: int,
    payload: schemas.ActionItemIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _owned_meeting(db, meeting_id, user.id)
    item = models.ActionItem(
        meeting_id=meeting_id,
        text=payload.text,
        assignee=payload.assignee,
        due_date=payload.due_date,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=schemas.ActionItemOut)
def update_action_item(
    meeting_id: int,
    item_id: int,
    payload: schemas.ActionItemUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    item = _owned_item(db, meeting_id, item_id, user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action_item(
    meeting_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    item = _owned_item(db, meeting_id, item_id, user.id)
    db.delete(item)
    db.commit()
