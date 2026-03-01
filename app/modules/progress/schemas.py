from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UserProgressRead(BaseModel):
    id: int
    user_id: str
    quest_id: int
    state: str
    progress_payload: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime | None = None
    reward_claimed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProgressWithQuestRead(UserProgressRead):
    quest_slug: str | None = None
    quest_name: str | None = None
