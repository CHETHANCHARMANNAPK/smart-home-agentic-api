from fastapi import APIRouter
from app.agent.agent import SmartHomeAgent
from app.models.schemas import CommandRequest, AgentResponse
from app.tools.registry import TOOLS

router = APIRouter()
agent = SmartHomeAgent()


@router.post("/agent", response_model=AgentResponse, summary="Execute a natural-language smart-home command")
async def run_agent(request: CommandRequest) -> AgentResponse:
    return await agent.handle(request)


@router.get("/tools", summary="List available tools and their strict schemas")
async def list_tools():
    return {
        name: {
            "category": spec["category"],
            "read_only": spec["read_only"],
            "description": spec["description"],
            "input_schema": spec["input_model"].model_json_schema(),
            "output_schema": spec["output_model"].model_json_schema(),
        }
        for name, spec in TOOLS.items()
    }
