from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    command: str = Field(min_length=1, max_length=1000, description="Natural-language home command")
    session_id: str | None = Field(default=None, max_length=100)

    @field_validator("command")
    @classmethod
    def command_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("command must contain non-whitespace text")
        return value


class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: str
    purpose: str
    category: Literal["status", "action", "verification"]
    arguments: dict[str, Any] = Field(default_factory=dict)


class AgentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: str
    rationale: str
    steps: list[PlanStep]


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: str
    category: Literal["status", "action", "verification"] | None = None
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    duration_ms: float | None = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str
    success: bool
    command: str
    intent: str
    planner: str
    plan: AgentPlan
    execution_trace: list[ToolResult]
    response: str
    safety_intervention: bool = False


class HardwareWindowPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    window_id: str
    status: Literal["open", "closed"]


class HardwareLightPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    room_id: str
    on: bool
