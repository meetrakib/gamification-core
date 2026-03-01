from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RuleType(str, Enum):
    TRADE_COUNT = "trade_count"
    VOLUME = "volume"
    SIGNUP = "signup"


class RuleResult(BaseModel):
    new_progress: dict[str, Any] = Field(default_factory=dict)
    completed: bool = False
