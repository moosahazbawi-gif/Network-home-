from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class BootstrapRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class TransferCreate(BaseModel):
    url: str = Field(min_length=8, max_length=4096)
    @field_validator("url")
    @classmethod
    def normalize_url(cls, value: str) -> str:
        return value.strip()

class TransferOut(BaseModel):
    id: int
    user_id: int
    source_url: str
    status: str
    safe_filename: Optional[str] = None
    stored_filename: Optional[str] = None
    content_type: Optional[str] = None
    sha256: Optional[str] = None
    byte_size: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
