import time
from app.models.schemas import AgentPlan, ToolResult
from app.tools.registry import TOOLS


class PolicyViolation(Exception):
    pass


class AgentExecutor:
    """Deterministic, policy-constrained tool executor.

    The planner/LLM proposes a plan. This class is the trust boundary: it
    validates tool schemas and prevents action tools from executing until their
    required observations have succeeded.
    """

    STATUS_REQUIREMENTS = {
        "lock_doors": {"get_window_status", "get_door_status"},
        "turn_off_lights": {"get_light_status"},
    }

    async def run(self, plan: AgentPlan) -> tuple[list[ToolResult], bool, str | None]:
        trace: list[ToolResult] = []
        successful_status: set[str] = set()

        for step in plan.steps:
            spec = TOOLS.get(step.tool)
            if not spec:
                return trace, False, f"Unknown tool requested: {step.tool}"
            # Verification steps intentionally reuse read-only status tools.
            if step.category == "action" and spec["category"] != "action":
                return trace, False, f"Tool category mismatch for {step.tool}."
            if step.category == "status" and spec["category"] != "status":
                return trace, False, f"Tool category mismatch for {step.tool}."
            if step.category == "verification" and not spec["read_only"]:
                return trace, False, f"Verification tool must be read-only: {step.tool}."

            if step.category == "action":
                # Global invariant: every action must be preceded by at least one
                # successful observation. Specific actions can require additional
                # observations below.
                if not successful_status:
                    return trace, True, (
                        f"Safety policy blocked {step.tool}: no successful status observation "
                        "has been completed before the action."
                    )
                required = self.STATUS_REQUIREMENTS.get(step.tool, set())
                missing = required - successful_status
                if missing:
                    return trace, True, (
                        f"Safety policy blocked {step.tool}: required status checks "
                        f"were not completed ({', '.join(sorted(missing))})."
                    )
                if not self._precondition_passed(step.tool, trace):
                    return trace, True, self._precondition_message(step.tool, trace)

            result = await self._call(step.tool, step.arguments)
            trace.append(result)
            if not result.success:
                return trace, False, f"Tool {step.tool} failed: {result.error or 'unknown error'}"

            if step.category == "status" or (step.category == "verification" and spec["read_only"]):
                successful_status.add(step.tool)

            if step.category == "verification" and not self._verification_passed(step.tool, result.data, plan.intent):
                return trace, True, f"Verification failed for {step.tool}; the desired state was not confirmed."

        return trace, False, None

    @staticmethod
    def _precondition_passed(tool: str, trace: list[ToolResult]) -> bool:
        if tool == "lock_doors":
            windows = next((x for x in reversed(trace) if x.tool == "get_window_status" and x.success), None)
            return bool(windows and windows.data.get("all_closed") is True)
        return True

    @staticmethod
    def _precondition_message(tool: str, trace: list[ToolResult]) -> str:
        if tool == "lock_doors":
            return "Security sequence stopped because one or more windows are open. Doors were not locked."
        return f"Safety precondition for {tool} was not satisfied."

    @staticmethod
    def _verification_passed(tool: str, data: dict, intent: str) -> bool:
        if intent == "secure_house":
            if tool == "get_door_status":
                return data.get("all_locked", False) is True
            if tool == "get_light_status":
                return data.get("any_on", True) is False
        if intent == "lights_off" and tool == "get_light_status":
            return data.get("any_on", True) is False
        return True

    async def _call(self, tool_name: str, arguments: dict) -> ToolResult:
        spec = TOOLS.get(tool_name)
        if not spec:
            return ToolResult(tool=tool_name, success=False, error="Tool not found")
        started = time.perf_counter()
        try:
            validated = spec["input_model"](**arguments)
            output = await spec["handler"](validated)
            return ToolResult(
                tool=tool_name,
                category=spec["category"],
                success=True,
                data=output.model_dump(),
                duration_ms=round((time.perf_counter() - started) * 1000, 3),
            )
        except Exception as exc:
            return ToolResult(
                tool=tool_name,
                category=spec["category"],
                success=False,
                error=str(exc),
                duration_ms=round((time.perf_counter() - started) * 1000, 3),
            )
