from pydantic import BaseModel


class TravelRequest(BaseModel):
    message: str
    session_id: str | None = None


class SessionSummary(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str


class SessionDetail(BaseModel):
    session_id: str
    title: str
    answer: str
    created_at: str
    updated_at: str
