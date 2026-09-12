import pytest
from app.agent.agent import SmartHomeAgent
from app.agent.executor import AgentExecutor
from app.mock_hardware.state import home_state
from app.models.schemas import AgentPlan, PlanStep


@pytest.fixture(autouse=True)
def reset_state():
    home_state.reset()


@pytest.mark.asyncio
async def test_secure_house_happy_path():
    result = await SmartHomeAgent().handle(type("R", (), {"command": "I'm heading to bed, secure the house."})())
    assert result.success is True
    assert result.intent == "secure_house"
    assert all(home_state.doors.values())
    assert not any(home_state.lights.values())
    assert [x.tool for x in result.execution_trace] == [
        "get_window_status", "get_door_status", "get_light_status", "lock_doors", "turn_off_lights",
        "get_door_status", "get_light_status",
    ]


@pytest.mark.asyncio
async def test_open_window_blocks_action():
    home_state.windows["bedroom"] = "open"
    result = await SmartHomeAgent().handle(type("R", (), {"command": "Secure the house"})())
    assert result.success is False
    assert result.safety_intervention is True
    assert all(v is False for v in home_state.doors.values())
    assert all(v is True for v in home_state.lights.values())
    assert all(x.tool != "lock_doors" for x in result.execution_trace)


@pytest.mark.asyncio
async def test_unknown_command_is_rejected():
    result = await SmartHomeAgent().handle(type("R", (), {"command": "Order me a pizza"})())
    assert result.success is False
    assert result.intent == "unknown"


@pytest.mark.asyncio
async def test_lights_only_checks_status_before_action():
    result = await SmartHomeAgent().handle(type("R", (), {"command": "Please turn off the lights"})())
    assert result.success is True
    assert [x.tool for x in result.execution_trace] == [
        "get_light_status", "turn_off_lights", "get_light_status"
    ]


@pytest.mark.asyncio
async def test_executor_blocks_action_without_required_status():
    plan = AgentPlan(
        intent="secure_house",
        rationale="malicious/incomplete plan",
        steps=[PlanStep(tool="lock_doors", purpose="lock", category="action")],
    )
    trace, intervention, error = await AgentExecutor().run(plan)
    assert intervention is True
    assert "status observation" in error
    assert trace == []
