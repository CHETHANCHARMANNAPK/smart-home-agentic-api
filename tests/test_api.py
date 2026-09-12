from fastapi.testclient import TestClient
from app.main import app
from app.mock_hardware.state import home_state


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_tools_endpoint_exposes_strict_schemas():
    with TestClient(app) as client:
        response = client.get("/api/v1/tools")
        assert response.status_code == 200
        tools = response.json()
        assert "get_window_status" in tools
        assert "lock_doors" in tools
        assert tools["lock_doors"]["input_schema"]["additionalProperties"] is False


def test_agent_endpoint():
    home_state.reset()
    with TestClient(app) as client:
        response = client.post("/api/v1/agent", json={"command": "secure the house"})
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["intent"] == "secure_house"
        assert body["request_id"]
        assert body["planner"] == "local-mock"
