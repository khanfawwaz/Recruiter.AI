"""
SQLAlchemy ORM models matching the PRD database schema.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, Text, TIMESTAMP, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ─── Recruiters (Auth) ────────────────────────────────────────────────────────

class Recruiter(Base):
    __tablename__ = "recruiters"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(Text, unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=False)
    full_name = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


# ─── Jobs ─────────────────────────────────────────────────────────────────────

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(Text, nullable=False)
    jd_text = Column(Text)
    required_skills = Column(JSONB, default=list)
    nice_to_have_skills = Column(JSONB, default=list)
    min_experience = Column(Integer)
    max_experience = Column(Integer)
    role_level = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    resumes = relationship("Resume", back_populates="job", cascade="all, delete-orphan")


# ─── Resumes ──────────────────────────────────────────────────────────────────

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text)
    email = Column(Text)
    total_experience_years = Column(Integer)
    skills = Column(JSONB, default=list)
    education = Column(Text)
    raw_text = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    job = relationship("Job", back_populates="resumes")
    evaluation = relationship("Evaluation", back_populates="resume", uselist=False, cascade="all, delete-orphan")
    approval = relationship("Approval", back_populates="resume", uselist=False, cascade="all, delete-orphan")


# ─── Evaluations ──────────────────────────────────────────────────────────────

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True)
    skill_score = Column(Integer, default=0)
    experience_score = Column(Integer, default=0)
    project_score = Column(Integer, default=0)
    education_score = Column(Integer, default=0)
    role_score = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    verdict = Column(Text)
    flags = Column(Text)
    reasoning = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    resume = relationship("Resume", back_populates="evaluation")


# ─── Approvals ────────────────────────────────────────────────────────────────

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True)
    final_decision = Column(Text)          # Interview / Reject / Hold
    recruiter_notes = Column(Text)
    approved_at = Column(TIMESTAMP, server_default=func.now())

    resume = relationship("Resume", back_populates="approval")
