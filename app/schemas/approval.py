from typing import Optional
from pydantic import BaseModel
from enum import Enum


class FinalDecision(str, Enum):
    interview = "Interview"
    reject = "Reject"
    hold = "Hold"


class ApprovalCreate(BaseModel):
    final_decision: FinalDecision
    recruiter_notes: Optional[str] = ""


class ApprovalRead(BaseModel):
    id: int
    resume_id: int
    final_decision: str
    recruiter_notes: Optional[str] = None

    model_config = {"from_attributes": True}
