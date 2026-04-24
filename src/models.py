from datetime import datetime
from typing import Any
from pydantic import BaseModel, field_validator


class Event(BaseModel):
    topic: str
    event_id: str
    timestamp: str
    source: str
    payload: dict[str, Any] = {}

    @field_validator("topic", "event_id", "source")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field tidak boleh kosong")
        return v.strip()

    @field_validator("timestamp")
    @classmethod
    def valid_iso8601(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"timestamp '{v}' bukan ISO 8601 yang valid")
        return v


class PublishRequest(BaseModel):
    events: list[Event]


class PublishResponse(BaseModel):
    received: int
    accepted: int
    duplicates: int


class StatsResponse(BaseModel):
    received: int
    unique_processed: int
    duplicate_dropped: int
    topics: list[str]
    uptime_seconds: float