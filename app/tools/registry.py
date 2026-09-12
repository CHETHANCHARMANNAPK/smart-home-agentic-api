from typing import Any, Awaitable, Callable
from pydantic import BaseModel

from app.tools.schemas import (
    EmptyInput, DoorActionInput, LightActionInput,
    WindowStatusOutput, DoorStatusOutput, LightStatusOutput, ActionOutput,
)
from app.mock_hardware.state import home_state

ToolHandler = Callable[[BaseModel], Awaitable[BaseModel]]


async def get_window_status(_: EmptyInput) -> WindowStatusOutput:
    windows = [{"id": k, "status": v} for k, v in home_state.windows.items()]
    return WindowStatusOutput(
        windows=windows,
        all_closed=all(x["status"] == "closed" for x in windows),
    )


async def get_door_status(_: EmptyInput) -> DoorStatusOutput:
    doors = [{"id": k, "locked": v} for k, v in home_state.doors.items()]
    return DoorStatusOutput(
        doors=doors,
        all_locked=all(x["locked"] for x in doors),
    )


async def get_light_status(_: EmptyInput) -> LightStatusOutput:
    lights = [{"id": k, "on": v} for k, v in home_state.lights.items()]
    return LightStatusOutput(
        lights=lights,
        any_on=any(x["on"] for x in lights),
    )


async def lock_doors(request: DoorActionInput) -> ActionOutput:
    targets = request.door_ids or list(home_state.doors.keys())
    unknown = [x for x in targets if x not in home_state.doors]
    if unknown:
        return ActionOutput(success=False, affected=[], message=f"Unknown door(s): {unknown}")
    for door in targets:
        home_state.doors[door] = True
    return ActionOutput(success=True, affected=targets, message="Requested doors locked")


async def turn_off_lights(request: LightActionInput) -> ActionOutput:
    targets = request.room_ids or list(home_state.lights.keys())
    unknown = [x for x in targets if x not in home_state.lights]
    if unknown:
        return ActionOutput(success=False, affected=[], message=f"Unknown room(s): {unknown}")
    for room in targets:
        home_state.lights[room] = False
    return ActionOutput(success=True, affected=targets, message="Requested lights turned off")


TOOLS: dict[str, dict[str, Any]] = {
    "get_window_status": {
        "input_model": EmptyInput, "output_model": WindowStatusOutput,
        "handler": get_window_status, "category": "status", "read_only": True,
        "description": "Read all window states. Required safety check before secure-house actions.",
    },
    "get_door_status": {
        "input_model": EmptyInput, "output_model": DoorStatusOutput,
        "handler": get_door_status, "category": "status", "read_only": True,
        "description": "Read all door lock states.",
    },
    "get_light_status": {
        "input_model": EmptyInput, "output_model": LightStatusOutput,
        "handler": get_light_status, "category": "status", "read_only": True,
        "description": "Read all light states.",
    },
    "lock_doors": {
        "input_model": DoorActionInput, "output_model": ActionOutput,
        "handler": lock_doors, "category": "action", "read_only": False,
        "description": "Lock selected doors or all doors.",
    },
    "turn_off_lights": {
        "input_model": LightActionInput, "output_model": ActionOutput,
        "handler": turn_off_lights, "category": "action", "read_only": False,
        "description": "Turn off selected rooms or all lights.",
    },
}
