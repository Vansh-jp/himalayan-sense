from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[\w\.\+\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z0-9]+$"


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., pattern=EMAIL_PATTERN)
    phone: Optional[str] = Field(None, max_length=30)
    district: Optional[str] = Field("Dehradun", max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)
    role: Optional[str] = Field("citizen", pattern="^(citizen|admin)$")


class UserLogin(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone: Optional[str] = None
    district: Optional[str] = None


class UserOut(UserBase):
    id: UUID
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str
