import uuid
from app.agent.executor import AgentExecutor
from app.agent.planner import build_planner
from app.models.schemas import AgentResponse, CommandRequest


class SmartHomeAgent:
    def __init__(self):
        self.planner = build_planner()

    async def handle(self, request: CommandRequest) -> AgentResponse:
        request_id = str(uuid.uuid4())
        plan = await self.planner.plan(request.command)
        if plan.intent == "unknown" or not plan.steps:
            return AgentResponse(
                request_id=request_id,
                success=False,
                command=request.command,
                intent="unknown",
                planner=self.planner.name,
                plan=plan,
                execution_trace=[],
                response="I couldn't map that request to a supported smart-home action.",
            )

        trace, intervention, error = await AgentExecutor().run(plan)
        if intervention and error:
            return AgentResponse(
                request_id=request_id,
                success=False,
                command=request.command,
                intent=plan.intent,
                planner=self.planner.name,
                plan=plan,
                execution_trace=trace,
                response=error,
                safety_intervention=True,
            )
        if error:
            return AgentResponse(
                request_id=request_id,
                success=False,
                command=request.command,
                intent=plan.intent,
                planner=self.planner.name,
                plan=plan,
                execution_trace=trace,
                response=f"I could not complete the request. {error}",
            )

        messages = {
            "secure_house": "House secured successfully: all doors are locked and all lights are off.",
            "lights_off": "The lights are off.",
        }
        return AgentResponse(
            request_id=request_id,
            success=True,
            command=request.command,
            intent=plan.intent,
            planner=self.planner.name,
            plan=plan,
            execution_trace=trace,
            response=messages.get(plan.intent, "Request completed."),
        )
