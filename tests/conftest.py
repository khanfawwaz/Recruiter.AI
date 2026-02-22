"""
Pytest configuration and fixtures.
Overrides DATABASE_URL to use an in-memory SQLite for all tests.
"""
import os
import pytest

# Use SQLite in-memory for tests BEFORE the app is imported
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ["SECRET_KEY"] = "test-secret-key-for-tests-only"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once before the full test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up test DB file
    if os.path.exists("test.db"):
        os.remove("test.db")


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
