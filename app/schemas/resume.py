from typing import Optional, List
from pydantic import BaseModel


class ResumeRead(BaseModel):
    id: int
    job_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    total_experience_years: Optional[int] = None
    skills: Optional[List[str]] = []
    education: Optional[str] = None

    model_config = {"from_attributes": True}


class ResumeUploadResult(BaseModel):
    candidate_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    total_score: int
    verdict: str
