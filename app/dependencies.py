"""
FastAPI dependency injection helpers.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import decode_access_token
from app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_recruiter(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Recruiter:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exc

    recruiter_id: int = payload.get("sub")
    if recruiter_id is None:
        raise credentials_exc

    recruiter = db.query(models.Recruiter).filter(models.Recruiter.id == int(recruiter_id)).first()
    if recruiter is None:
        raise credentials_exc

    return recruiter
