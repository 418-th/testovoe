from sqlmodel import SQLModel, Field

import enum

from sqlalchemy import Column, String, DECIMAL
from sqlalchemy import Enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from decimal import Decimal


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class BetState(str, enum.Enum):
    not_completed = "not_completed"
    won = "won"
    lost = "lost"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int = Field(default=None, nullable=False, primary_key=True, index=True)
    username: str = Field(index=True, nullable=False, sa_column=Column(String, unique=True))
    email: str = Field(index=True, nullable=False, sa_column=Column(String, unique=True))
    hashed_password: str = Field(sa_column=Column(String))

    # bets: list["Bet"] = relationship("Bet", back_populates="user")

    def verify_password(self, password: str):
        return pwd_context.verify(password, self.hashed_password)

    def set_password(self, password: str):
        self.hashed_password = pwd_context.hash(password)


class Bet(SQLModel, table=True):
    __tablename__ = "bets"

    id: int = Field(default=None, primary_key=True, index=True)
    event_uuid: str = Field(sa_column=Column(String))
    value: Decimal = Field(sa_column=Column(DECIMAL))
    odds: Decimal = Field(sa_column=Column(DECIMAL))
    state: BetState = Field(default=BetState.not_completed, sa_column=Column(Enum(BetState)))

    user_id: int = Field(nullable=False)
    # user_id: int = Field(ForeignKey("users.id"))
    # user: User = relationship("User", back_populates="bets")

