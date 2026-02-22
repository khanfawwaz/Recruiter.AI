from typing import Optional, List
from pydantic import BaseModel


class JobCreate(BaseModel):
    job_title: str


class JobCriteria(BaseModel):
    required_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    role_level: Optional[str] = None


class JobRead(BaseModel):
    id: int
    job_title: str
    required_skills: Optional[List[str]] = []
    nice_to_have_skills: Optional[List[str]] = []
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    role_level: Optional[str] = None

    model_config = {"from_attributes": True}
