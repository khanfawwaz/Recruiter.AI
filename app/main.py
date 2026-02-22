"""
Recruiter AI – DB-free MVP backend.

Architecture:
  • No database, no auth, no email.
  • Jobs and results are stored in a per-process in-memory dict (SESSION_STORE).
  • Each upload creates a session_id (uuid). The frontend passes that back
    to retrieve results and finalize.

Routes:
  POST /analyze          – Upload JD + resumes, run Gemini, return ranked results
  POST /override         – Update a candidate's decision in the session
  POST /finalize/{sid}   – Simulate email sending, return preview data
  GET  /session/{sid}    – Retrieve stored session results
  GET  /health           – Health check
"""

import logging
import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.pdf_service import read_upload_file, extract_text
from app.services.llm_service import parse_jd, parse_resume, evaluate_candidate, QuotaError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)

# ── In-memory session store ────────────────────────────────────────────────────
# { session_id: { "job_title": str, "criteria": dict, "candidates": [...] } }
SESSION_STORE: Dict[str, dict] = {}


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Recruiter AI – DB-free MVP. Gemini-powered resume evaluation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": settings.APP_VERSION}


# ── POST /analyze ──────────────────────────────────────────────────────────────
@app.post("/analyze", tags=["Analyze"])
async def analyze(
    job_title: str = Form(...),
    jd_pdf: UploadFile = File(...),
    resumes: List[UploadFile] = File(...),
):
    """
    Upload a JD (PDF) + one or more resume PDFs.
    Parses with Gemini and returns ranked candidates.
    Returns a session_id to use for overrides and finalize.
    """
    logger.info(f"analyze: job_title='{job_title}', resumes={[r.filename for r in resumes]}")

    # 1. Parse JD
    try:
        jd_content = await read_upload_file(jd_pdf)
        jd_text = extract_text(jd_content, jd_pdf.filename)
        criteria = parse_jd(jd_text, filename=jd_pdf.filename)
    except HTTPException:
        raise
    except QuotaError:
        raise HTTPException(
            status_code=503,
            detail="⚠️ Gemini API quota exceeded. Your free-tier limit has been reached. Please wait for it to reset (resets daily at midnight Pacific Time) or set DEMO_MODE=true in your .env to use mock results."
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"JD processing failed: {exc}")

    # 2. Parse + evaluate each resume
    candidates = []
    errors = []
    for upload in resumes:
        filename = upload.filename
        try:
            content = await read_upload_file(upload)
            resume_text = extract_text(content, filename)
            candidate_data = parse_resume(resume_text, filename=filename)
            eval_data = evaluate_candidate(criteria, candidate_data, filename=filename)

            candidate_id = str(uuid.uuid4())
            candidates.append({
                "candidate_id": candidate_id,
                "filename": filename,
                "name": candidate_data.get("name"),
                "email": candidate_data.get("email"),
                "experience_years": candidate_data.get("total_experience_years"),
                "skills": candidate_data.get("skills", []),
                "education": candidate_data.get("education"),
                "total_score": eval_data["total_score"],
                "skill_score": eval_data["skill_score"],
                "experience_score": eval_data["experience_score"],
                "project_score": eval_data["project_score"],
                "education_score": eval_data["education_score"],
                "role_score": eval_data["role_score"],
                "verdict": eval_data["verdict"],
                "flags": eval_data["flags"],
                "reasoning": eval_data["reasoning"],
                # AI default decision
                "decision": (
                    "Interview" if eval_data["verdict"] in ("Strong Yes", "Yes")
                    else "Hold" if eval_data["verdict"] == "Maybe"
                    else "Reject"
                ),
            })
            logger.info(f"  {filename}: score={eval_data['total_score']}, verdict={eval_data['verdict']}")
        except QuotaError:
            raise HTTPException(
                status_code=503,
                detail="⚠️ Gemini API quota exceeded. Your free-tier limit has been reached. Please wait for it to reset (resets daily at midnight Pacific Time) or set DEMO_MODE=true in your .env to use mock results."
            )
        except HTTPException as exc:
            errors.append({"filename": filename, "error": exc.detail})
        except Exception as exc:
            logger.error(f"  {filename} failed: {exc}")
            errors.append({"filename": filename, "error": str(exc)})

    # Sort by score desc
    candidates.sort(key=lambda c: c["total_score"], reverse=True)

    # 3. Store session
    session_id = str(uuid.uuid4())
    SESSION_STORE[session_id] = {
        "job_title": job_title,
        "criteria": criteria,
        "candidates": candidates,
    }

    return {
        "session_id": session_id,
        "job_title": job_title,
        "total_candidates": len(candidates),
        "candidates": candidates,
        "errors": errors,
    }


# ── GET /session/{sid} ────────────────────────────────────────────────────────
@app.get("/session/{session_id}", tags=["Session"])
def get_session(session_id: str):
    """Retrieve stored results for a session."""
    session = SESSION_STORE.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


# ── POST /override ─────────────────────────────────────────────────────────────
@app.post("/override", tags=["Override"])
def override_decision(payload: dict):
    """
    Update a candidate's decision within a session.
    Body: { session_id, candidate_id, decision: "Interview"|"Hold"|"Reject" }
    """
    session_id   = payload.get("session_id")
    candidate_id = payload.get("candidate_id")
    decision     = payload.get("decision")

    if decision not in ("Interview", "Hold", "Reject"):
        raise HTTPException(status_code=400, detail="decision must be Interview, Hold, or Reject.")

    session = SESSION_STORE.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    for c in session["candidates"]:
        if c["candidate_id"] == candidate_id:
            c["decision"] = decision
            return {"ok": True, "candidate_id": candidate_id, "decision": decision}

    raise HTTPException(status_code=404, detail="Candidate not found in session.")


# ── POST /finalize/{sid} ───────────────────────────────────────────────────────
@app.post("/finalize/{session_id}", tags=["Finalize"])
def finalize(session_id: str):
    """
    MVP simulation – no emails are actually sent.
    Returns preview data for the email screen.
    """
    session = SESSION_STORE.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    job_title = session["job_title"]
    candidates = session["candidates"]

    interview_candidates = [c for c in candidates if c["decision"] == "Interview"]
    hold_candidates      = [c for c in candidates if c["decision"] == "Hold"]
    reject_candidates    = [c for c in candidates if c["decision"] == "Reject"]

    previews = []
    for c in interview_candidates:
        previews.append({
            "candidate_id": c["candidate_id"],
            "name": c["name"],
            "email": c["email"],
            "decision": "Interview",
            "email_subject": f"Interview Invitation — {job_title}",
            "email_body": (
                f"Dear {c['name'] or 'Candidate'},\n\n"
                f"Thank you for your interest in the {job_title} position. "
                f"We were impressed with your background and would like to invite you for an interview.\n\n"
                f"Please confirm your availability for the proposed time below.\n\n"
                f"Best regards,\nHiring Team"
            ),
            "simulated": True,
        })

    logger.info(
        f"finalize: session={session_id}, interview={len(interview_candidates)}, "
        f"hold={len(hold_candidates)}, reject={len(reject_candidates)}"
    )

    return {
        "session_id": session_id,
        "job_title": job_title,
        "simulated": True,
        "summary": {
            "interview": len(interview_candidates),
            "hold": len(hold_candidates),
            "reject": len(reject_candidates),
        },
        "email_previews": previews,
    }


# ── Global exception handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled(request, exc):
    logger.error(f"Unhandled: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
