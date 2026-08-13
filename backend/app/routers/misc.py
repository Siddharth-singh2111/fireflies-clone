"""Small support endpoints: current user + tag list (for filters)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/api", tags=["misc"])


@router.get("/me", response_model=schemas.UserOut)
def current_user(user: models.User = Depends(get_current_user)):
    return user


@router.get("/tags", response_model=list[schemas.TagOut])
def list_tags(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Tag).order_by(models.Tag.name).all()
