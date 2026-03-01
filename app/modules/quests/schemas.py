from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QuestBase(BaseModel):
    slug: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    quest_type: str = "repeated"
    rules: dict[str, Any] = Field(default_factory=dict)
    reward: dict[str, Any] = Field(default_factory=dict)
    schedule_start: datetime | None = None
    schedule_end: datetime | None = None
    is_active: bool = True


class QuestCreate(QuestBase):
    pass


class QuestUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    quest_type: str | None = None
    rules: dict[str, Any] | None = None
    reward: dict[str, Any] | None = None
    schedule_start: datetime | None = None
    schedule_end: datetime | None = None
    is_active: bool | None = None


class QuestRead(QuestBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
