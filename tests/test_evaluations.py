"""
Tests for the Evaluations (recruiter override) endpoint.
"""
import io
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)

MOCK_JD_CRITERIA = {
    "required_skills": ["Python"],
    "nice_to_have_skills": [],
    "min_experience": 2,
    "max_experience": 5,
    "role_level": "Junior",
}
MOCK_CANDIDATE = {
    "name": "John Smith",
    "email": "john@example.com",
    "total_experience_years": 3,
    "skills": ["Python"],
    "education": "B.Sc. CS",
}
MOCK_EVALUATION = {
    "skill_score": 30,
    "experience_score": 15,
    "project_score": 10,
    "education_score": 7,
    "role_score": 10,
    "total_score": 72,
    "verdict": "Yes",
    "flags": "",
    "reasoning": "Good fit.",
}


def get_headers_and_resume_id():
    # Register + login
    client.post("/auth/register", json={"email": "eval_test@r.ai", "password": "Pass123!", "full_name": "Eval Tester"})
    token_resp = client.post("/auth/token", data={"username": "eval_test@r.ai", "password": "Pass123!"})
    headers = {"Authorization": f"Bearer {token_resp.json()['access_token']}"}

    # Create job
    with (
        patch("app.services.pdf_service.pdfplumber.open") as mp,
        patch("app.services.llm_service.parse_jd") as mj,
    ):
        mp.return_value.__enter__.return_value.pages = [MagicMock(extract_text=lambda: "JD text")]
        mj.return_value = MOCK_JD_CRITERIA
        job_resp = client.post("/jobs", headers=headers, data={"job_title": "Dev"},
                               files={"jd_pdf": ("jd.pdf", io.BytesIO(b"%PDF"), "application/pdf")})
    job_id = job_resp.json()["data"]["job_id"]

    # Upload resume
    with (
        patch("app.services.pdf_service.pdfplumber.open") as mp,
        patch("app.services.llm_service.parse_resume") as mpr,
        patch("app.services.llm_service.evaluate_candidate") as mev,
    ):
        mp.return_value.__enter__.return_value.pages = [MagicMock(extract_text=lambda: "Resume text")]
        mpr.return_value = MOCK_CANDIDATE
        mev.return_value = MOCK_EVALUATION
        res_resp = client.post(f"/jobs/{job_id}/resumes", headers=headers,
                               files={"resumes": ("cv.pdf", io.BytesIO(b"%PDF"), "application/pdf")})

    resume_id = res_resp.json()["data"]["processed"][0]["candidate_id"]
    return headers, resume_id


def test_recruiter_override_interview():
    headers, resume_id = get_headers_and_resume_id()
    resp = client.post(
        f"/evaluations/{resume_id}/override",
        headers=headers,
        json={"final_decision": "Interview", "recruiter_notes": "Good cultural fit."},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["final_decision"] == "Interview"


def test_recruiter_override_reject():
    headers, resume_id = get_headers_and_resume_id()
    resp = client.post(
        f"/evaluations/{resume_id}/override",
        headers=headers,
        json={"final_decision": "Reject", "recruiter_notes": "Not enough experience."},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["final_decision"] == "Reject"


def test_override_upsert():
    """Calling override twice should update, not create a duplicate."""
    headers, resume_id = get_headers_and_resume_id()
    client.post(f"/evaluations/{resume_id}/override", headers=headers,
                json={"final_decision": "Hold", "recruiter_notes": ""})
    resp = client.post(f"/evaluations/{resume_id}/override", headers=headers,
                       json={"final_decision": "Interview", "recruiter_notes": "Changed mind."})
    assert resp.status_code == 200
    assert resp.json()["data"]["final_decision"] == "Interview"


def test_override_nonexistent_resume():
    client.post("/auth/register", json={"email": "ov2@r.ai", "password": "Pass123!", "full_name": "X"})
    token_resp = client.post("/auth/token", data={"username": "ov2@r.ai", "password": "Pass123!"})
    headers = {"Authorization": f"Bearer {token_resp.json()['access_token']}"}
    resp = client.post("/evaluations/99999/override", headers=headers,
                       json={"final_decision": "Reject", "recruiter_notes": ""})
    assert resp.status_code == 404
