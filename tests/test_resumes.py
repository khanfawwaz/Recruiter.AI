"""
Tests for the Resumes router and Evaluation flow.
"""
import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)

MOCK_JD_CRITERIA = {
    "required_skills": ["Python", "FastAPI"],
    "nice_to_have_skills": ["Docker"],
    "min_experience": 2,
    "max_experience": 6,
    "role_level": "Mid",
}

MOCK_CANDIDATE = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "total_experience_years": 4,
    "skills": ["Python", "FastAPI", "Docker"],
    "education": "B.Sc. Computer Science, MIT",
}

MOCK_EVALUATION = {
    "skill_score": 36,
    "experience_score": 18,
    "project_score": 12,
    "education_score": 8,
    "role_score": 13,
    "total_score": 87,
    "verdict": "Strong Yes",
    "flags": "",
    "reasoning": "Strong skills match and solid experience.",
}


def get_auth_headers():
    client.post("/auth/register", json={
        "email": "resume_test@recruiter.ai",
        "password": "TestPass123!",
        "full_name": "Resume Tester",
    })
    resp = client.post("/auth/token", data={
        "username": "resume_test@recruiter.ai",
        "password": "TestPass123!",
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def create_test_job(headers):
    with (
        patch("app.services.pdf_service.pdfplumber.open") as mock_pdf,
        patch("app.services.llm_service.parse_jd") as mock_jd,
    ):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Python FastAPI developer role"
        mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
        mock_jd.return_value = MOCK_JD_CRITERIA

        resp = client.post(
            "/jobs",
            headers=headers,
            data={"job_title": "Backend Dev"},
            files={"jd_pdf": ("jd.pdf", io.BytesIO(b"%PDF fake"), "application/pdf")},
        )
    return resp.json()["data"]["job_id"]


@patch("app.services.pdf_service.pdfplumber.open")
@patch("app.services.llm_service.parse_resume")
@patch("app.services.llm_service.evaluate_candidate")
def test_upload_resume(mock_eval, mock_parse, mock_pdf):
    """POST /jobs/{job_id}/resumes should process a resume and return a score."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Jane Doe – Python developer with 4 years..."
    mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
    mock_parse.return_value = MOCK_CANDIDATE
    mock_eval.return_value = MOCK_EVALUATION

    headers = get_auth_headers()
    job_id = create_test_job(headers)

    resp = client.post(
        f"/jobs/{job_id}/resumes",
        headers=headers,
        files={"resumes": ("jane_doe.pdf", io.BytesIO(b"%PDF resume"), "application/pdf")},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    processed = data["data"]["processed"]
    assert len(processed) == 1
    assert processed[0]["total_score"] == 87
    assert processed[0]["name"] == "Jane Doe"


def test_upload_resume_to_missing_job():
    """Should return 404 when job doesn't exist."""
    headers = get_auth_headers()
    resp = client.post(
        "/jobs/99999/resumes",
        headers=headers,
        files={"resumes": ("cv.pdf", io.BytesIO(b"%PDF data"), "application/pdf")},
    )
    assert resp.status_code == 404
