"""
Auth router – register and login for recruiters.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.auth import hash_password, verify_password, create_access_token
from app.schemas.recruiter import RecruiterRegister, RecruiterRead, Token
from app.schemas.common import success

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RecruiterRegister, db: Session = Depends(get_db)):
    existing = db.query(models.Recruiter).filter(models.Recruiter.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A recruiter with this email already exists.",
        )
    recruiter = models.Recruiter(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(recruiter)
    db.commit()
    db.refresh(recruiter)
    return success(
        data=RecruiterRead.model_validate(recruiter).model_dump(),
        message="Recruiter registered successfully.",
    )


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    recruiter = db.query(models.Recruiter).filter(models.Recruiter.email == form_data.username).first()
    if not recruiter or not verify_password(form_data.password, recruiter.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": str(recruiter.id)})
    return {"access_token": token, "token_type": "bearer"}
