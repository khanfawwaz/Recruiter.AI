from typing import Optional
from pydantic import BaseModel


class EvaluationRead(BaseModel):
    id: int
    resume_id: int
    skill_score: int
    experience_score: int
    project_score: int
    education_score: int
    role_score: int
    total_score: int
    verdict: Optional[str] = None
    flags: Optional[str] = None
    reasoning: Optional[str] = None

    model_config = {"from_attributes": True}


class RankedCandidate(BaseModel):
    candidate_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    total_score: int
    skill_score: int
    experience_score: int
    project_score: int
    education_score: int
    role_score: int
    verdict: Optional[str] = None
    flags: Optional[str] = None
    final_decision: Optional[str] = None   # from approvals
