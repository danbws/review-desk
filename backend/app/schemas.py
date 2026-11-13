from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Credentials(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    password: str = Field(min_length=8, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    plan: str


class ReviewIn(BaseModel):
    title: str = Field(default="Untitled review", max_length=200)
    language: str = Field(default="auto", max_length=40)
    code: str = Field(min_length=1)


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    severity: str
    line: int | None
    title: str
    suggestion: str


class ReviewSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    language: str
    status: str
    created_at: datetime
    finding_count: int = 0


class ReviewDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    language: str
    code: str
    status: str
    provider: str
    summary: str
    created_at: datetime
    findings: list[FindingOut]


class UsageOut(BaseModel):
    plan: str
    period: str
    used: int
    limit: int
    remaining: int


class PlanOut(BaseModel):
    id: str
    name: str
    monthly_reviews: int
    price_usd_month: int


class CheckoutIn(BaseModel):
    plan: str


class CheckoutOut(BaseModel):
    plan: str
    status: str
    provider: str
    checkout_url: str | None = None
