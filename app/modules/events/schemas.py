from typing import Any

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=256)
    event_type: str = Field(..., min_length=1, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class EventOut(BaseModel):
    accepted: bool = True
    updated_progress_count: int = 0
