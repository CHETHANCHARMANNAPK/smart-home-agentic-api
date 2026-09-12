from copy import deepcopy
from dataclasses import dataclass, field
from typing import Literal

Status = Literal["open", "closed"]


@dataclass
class HomeState:
    windows: dict[str, Status] = field(default_factory=lambda: {
        "living_room": "closed", "bedroom": "closed", "kitchen": "closed",
    })
    doors: dict[str, bool] = field(default_factory=lambda: {
        "front_door": False, "back_door": False, "garage_door": False,
    })
    lights: dict[str, bool] = field(default_factory=lambda: {
        "living_room": True, "bedroom": True, "kitchen": True, "hallway": True,
    })

    def snapshot(self) -> dict:
        return deepcopy({"windows": self.windows, "doors": self.doors, "lights": self.lights})

    def reset(self) -> None:
        self.windows = {"living_room": "closed", "bedroom": "closed", "kitchen": "closed"}
        self.doors = {"front_door": False, "back_door": False, "garage_door": False}
        self.lights = {"living_room": True, "bedroom": True, "kitchen": True, "hallway": True}


home_state = HomeState()
