import enum

from typing import Optional, List

from pydantic import BaseModel


class EventState(str, enum.Enum):
    not_completed = "Not completed"
    first_won = "First won"
    second_won = "Second won"


class EventSchema(BaseModel):
    uuid: Optional[str]
    coefficient: float
    expiration_time: str
    state: EventState


class EventsListSchema(BaseModel):
    events: List[EventSchema]
