import enum

from uuid import UUID
from typing import Optional, List
from decimal import Decimal

from pydantic import BaseModel, EmailStr

from app import BetState


class UserSchema(BaseModel):
    username: str
    email: EmailStr
    hashed_password: Optional[str]


class UserCreateSchema(BaseModel):
    id: int


class BetCreateSchema(BaseModel):
    user_id: int
    event_uuid: str
    value: float


class BetSchema(BaseModel):
    event_uuid: str
    value: Decimal
    odds: Decimal
    state: BetState


class BetsListSchema(BaseModel):
    bets: List[BetSchema]


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
