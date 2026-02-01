from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserPublic(UserBase):
    id: int
    credits: int
    plan: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class WorksheetGenerateRequest(BaseModel):
    level: str = Field(pattern="^(A1|A2|B1|B2)$")
    topic: str
    age_group: str = Field(pattern="^(8-10|11-13|14-16|adult)$")
    duration: int = Field(ge=10, le=45)
    activity_types: list[str]
    theme_words: list[str] | None = None


class WorksheetGenerateResponse(BaseModel):
    title: str
    estimated_duration: str
    content: list[str]
    solutions: list[str]
    remaining_credits: int


class TokenData(BaseModel):
    user_id: Optional[int] = None
