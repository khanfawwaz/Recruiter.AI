"""
Tests for the Jobs router.
Uses an in-memory SQLite DB and mocks the LLM + PDF services.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io

from app.main import app

client = TestClient(app)


MOCK_JD_CRITERIA = {
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "nice_to_have_skills": ["Docker", "Redis"],
    "min_experience": 3,
    "max_experience": 7,
    "role_level": "Mid",
}

MOCK_TOKEN = None  # Will be set after auth


def get_auth_headers(client):
    """Register + login a test recruiter, return auth headers."""
    client.post("/auth/register", json={
        "email": "test@recruiter.ai",
        "password": "TestPass123!",
        "full_name": "Test Recruiter",
    })
    resp = client.post("/auth/token", data={
        "username": "test@recruiter.ai",
        "password": "TestPass123!",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@patch("app.services.pdf_service.pdfplumber.open")
@patch("app.services.llm_service.parse_jd")
def test_upload_job_description(mock_parse_jd, mock_pdf_open):
    """POST /jobs should create a job and return structured criteria."""
    # Mock pdfplumber
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "We are looking for a Python developer..."
    mock_pdf_open.return_value.__enter__.return_value.pages = [mock_page]

    # Mock Gemini
    mock_parse_jd.return_value = MOCK_JD_CRITERIA

    headers = get_auth_headers(client)
    pdf_bytes = b"%PDF-1.4 fake pdf content"

    resp = client.post(
        "/jobs",
        headers=headers,
        data={"job_title": "Python Backend Engineer"},
        files={"jd_pdf": ("jd.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert "job_id" in data["data"]
    assert data["data"]["required_skills"] == ["Python", "FastAPI", "PostgreSQL"]


@patch("app.services.pdf_service.pdfplumber.open")
@patch("app.services.llm_service.parse_jd")
def test_get_ranked_results_empty(mock_parse_jd, mock_pdf_open):
    """GET /jobs/{job_id}/results should return empty list for new job."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Backend engineer role..."
    mock_pdf_open.return_value.__enter__.return_value.pages = [mock_page]
    mock_parse_jd.return_value = MOCK_JD_CRITERIA

    headers = get_auth_headers(client)

    # Create a job first
    resp = client.post(
        "/jobs",
        headers=headers,
        data={"job_title": "Test Role"},
        files={"jd_pdf": ("jd.pdf", io.BytesIO(b"%PDF fakedata"), "application/pdf")},
    )
    job_id = resp.json()["data"]["job_id"]

    # Get results
    resp = client.get(f"/jobs/{job_id}/results", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["total_candidates"] == 0


def test_get_results_not_found():
    """Should return 404 for non-existent job."""
    headers = get_auth_headers(client)
    resp = client.get("/jobs/99999/results", headers=headers)
    assert resp.status_code == 404
