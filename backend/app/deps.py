"""Shared dependencies.

Auth is mocked per the assignment ("assume a default logged-in user"), so
`get_current_user` simply returns the single seeded user. Because it's modelled
as a dependency, swapping in real JWT/session auth later touches only this file.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.database import get_db


def get_current_user(db: Session = Depends(get_db)) -> models.User:
    user = db.query(models.User).order_by(models.User.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No default user found. Run the seed script.",
        )
    return user
