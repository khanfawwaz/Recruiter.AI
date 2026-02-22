from pydantic import BaseModel, EmailStr


class RecruiterRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class RecruiterRead(BaseModel):
    id: int
    email: str
    full_name: str | None = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
