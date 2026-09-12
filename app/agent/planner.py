import json
import os
from abc import ABC, abstractmethod

import httpx

from app.models.schemas import AgentPlan, PlanStep


class Planner(ABC):
    name = "planner"

    @abstractmethod
    async def plan(self, command: str) -> AgentPlan:
        raise NotImplementedError


def secure_plan() -> AgentPlan:
    return AgentPlan(
        intent="secure_house",
        rationale="The request implies bedtime or leaving and therefore securing the home.",
        steps=[
            PlanStep(tool="get_window_status", purpose="Check that every window is closed before security actions.", category="status"),
            PlanStep(tool="get_door_status", purpose="Inspect current door lock state.", category="status"),
            PlanStep(tool="get_light_status", purpose="Inspect lighting state before changing lights.", category="status"),
            PlanStep(tool="lock_doors", purpose="Lock all doors once safety checks pass.", category="action"),
            PlanStep(tool="turn_off_lights", purpose="Turn off all lights after security checks pass.", category="action"),
            PlanStep(tool="get_door_status", purpose="Verify that every door is locked.", category="verification"),
            PlanStep(tool="get_light_status", purpose="Verify that every light is off.", category="verification"),
        ],
    )


def lights_plan() -> AgentPlan:
    return AgentPlan(
        intent="lights_off",
        rationale="The request explicitly asks for the lights to be turned off.",
        steps=[
            PlanStep(tool="get_light_status", purpose="Inspect lighting state before acting.", category="status"),
            PlanStep(tool="turn_off_lights", purpose="Turn off active lights.", category="action"),
            PlanStep(tool="get_light_status", purpose="Verify that all lights are off.", category="verification"),
        ],
    )


class LocalIntentPlanner(Planner):
    """Deterministic no-key planner used for reliable evaluation and fallback."""

    name = "local-mock"

    async def plan(self, command: str) -> AgentPlan:
        text = command.lower().strip()
        secure_words = (
            "secure", "lock up", "lock the house", "secure the house",
            "heading to bed", "going to bed", "leaving the house", "bedtime",
            "i'm leaving", "im leaving", "going out",
        )
        lights_only = (
            "turn off the lights", "switch off the lights", "lights off",
            "turn the lights off", "turn off lights", "switch off lights",
        )
        if any(phrase in text for phrase in secure_words):
            return secure_plan()
        if any(phrase in text for phrase in lights_only):
            return lights_plan()
        return AgentPlan(intent="unknown", rationale="No supported smart-home intent was detected.", steps=[])


class LLMPlanner(Planner):
    """Optional OpenAI-compatible chat-completions planner.

    The LLM is untrusted: its output is validated as AgentPlan and later checked
    by the policy-constrained executor. If configuration is absent or the call
    fails, callers can fall back to LocalIntentPlanner.
    """

    name = "llm"

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def plan(self, command: str) -> AgentPlan:
        tools = []
        from app.tools.registry import TOOLS
        for name, spec in TOOLS.items():
            tools.append({
                "name": name,
                "category": spec["category"],
                "description": spec["description"],
                "input_schema": spec["input_model"].model_json_schema(),
            })
        system = (
            "You are a smart-home planning engine. Return ONLY valid JSON matching this schema: "
            '{"intent":"string","rationale":"string","steps":[{"tool":"string",'
            '"purpose":"string","category":"status|action|verification","arguments":{}}]}. '
            "Only use listed tools. Never invent tools. For secure_house, status checks must precede actions. "
            "Prefer get_window_status and get_door_status before locking doors; verify actions afterward. "
            f"Available tools: {json.dumps(tools)}"
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": command},
            ],
            "temperature": 0,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        return AgentPlan.model_validate_json(content)


def build_planner() -> Planner:
    provider = os.getenv("PLANNER_PROVIDER", "mock").lower()
    if provider == "llm":
        base_url = os.getenv("LLM_BASE_URL", "")
        api_key = os.getenv("LLM_API_KEY", "")
        model = os.getenv("LLM_MODEL", "")
        if base_url and api_key and model:
            return LLMPlanner(base_url, api_key, model)
    return LocalIntentPlanner()
