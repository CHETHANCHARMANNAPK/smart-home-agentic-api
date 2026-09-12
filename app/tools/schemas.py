from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyInput(StrictBase):
    pass


class DoorActionInput(StrictBase):
    door_ids: list[str] = Field(default_factory=list, description="Doors to lock; empty means all doors")


class LightActionInput(StrictBase):
    room_ids: list[str] = Field(default_factory=list, description="Rooms; empty means all lights")


class WindowStatus(StrictBase):
    id: str
    status: Literal["open", "closed"]


class WindowStatusOutput(StrictBase):
    windows: list[WindowStatus]
    all_closed: bool


class DoorStatus(StrictBase):
    id: str
    locked: bool


class DoorStatusOutput(StrictBase):
    doors: list[DoorStatus]
    all_locked: bool


class LightStatus(StrictBase):
    id: str
    on: bool


class LightStatusOutput(StrictBase):
    lights: list[LightStatus]
    any_on: bool


class ActionOutput(StrictBase):
    success: bool
    affected: list[str]
    message: str
