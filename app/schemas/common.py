"""Standard API response wrappers."""
from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    status: str = "success"
    data: Any = None
    message: str = ""


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str


def success(data: Any = None, message: str = "") -> dict:
    return {"status": "success", "data": data, "message": message}


def error(message: str) -> dict:
    return {"status": "error", "message": message}
