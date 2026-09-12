# Smart Home Agentic API

A safety-aware, asynchronous FastAPI proof-of-concept that converts vague natural-language home commands into structured multi-step plans, observes the simulated physical environment, executes validated hardware tools, and verifies the resulting state.

## Why this design

The central design principle is:

> **The planner proposes; the policy-constrained executor decides what may actually execute.**

An LLM is treated as an untrusted planner rather than a direct hardware controller. Every tool call is validated against a Pydantic schema, action tools are gated by required status observations, and important actions are followed by verification.

## Challenge coverage

| Requirement | Implementation |
|---|---|
| Async REST API | FastAPI `async` endpoint at `POST /api/v1/agent` |
| Natural-language intent | Local deterministic planner; optional OpenAI-compatible LLM planner |
| Multi-step agent loop | Plan → observe → policy check → act → verify |
| 3+ hardware tools | 5 mock tools in a typed registry |
| Strict JSON schemas | Pydantic models with `extra="forbid"` |
| Status before action | Executor policy requires status tools before every supported action |
| Physical-state reasoning | Window/door/light state is read before execution |
| Safety intervention | Open window blocks the security sequence |
| Architecture diagram | `docs/architecture.svg` and `docs/architecture.mmd` |
| Testing | Pytest + async tests + API tests |
| Voice flow | Architecture includes ASR and TTS adapters; challenge API accepts the ASR transcript |

## Architecture

```text
User Voice
    │
    ▼
  ASR
    │ transcript
    ▼
FastAPI /api/v1/agent
    │
    ▼
Planner (Local Mock or optional LLM)
    │ structured AgentPlan
    ▼
Policy-Constrained Executor
    │
    ├── Status tools ───────► Mock Home State
    │       │
    │       └── safety decision
    │
    ├── Action tools ───────► Mock Home State
    │
    └── Verification tools ─► Mock Home State
    │
    ▼
AgentResponse / execution trace
    │
    ▼
  TTS
    │
    ▼
User Voice
```

The rendered diagram is in `docs/architecture.svg`.

## Supported tools

### Status tools

- `get_window_status`
- `get_door_status`
- `get_light_status`

### Action tools

- `lock_doors`
- `turn_off_lights`

Every tool declares:

- input Pydantic model
- output Pydantic model
- category (`status`, `action`)
- read-only flag
- description

The `/api/v1/tools` endpoint exposes the generated JSON Schemas for evaluation.

## Agent behavior

### Happy path

Input:

```json
{"command":"I'm heading to bed, secure the house."}
```

Expected sequence:

```text
get_window_status
        ↓
get_door_status
        ↓
lock_doors
        ↓
turn_off_lights
        ↓
get_door_status  (verification)
        ↓
get_light_status (verification)
```

### Safety path

If `bedroom` is open:

```text
get_window_status
        ↓
all_closed = false
        ↓
SAFETY INTERVENTION
        ↓
lock_doors is NOT executed
turn_off_lights is NOT executed
```

This prevents the system from assuming that the physical environment is safe merely because the user requested a security action.

### Unsupported intent

For an unrelated request such as `Order me a pizza`, the planner returns `unknown` and no hardware tool is executed.

## Project structure

```text
smart-home-agent/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── routes.py
│   │   └── hardware_routes.py
│   ├── agent/
│   │   ├── agent.py
│   │   ├── planner.py
│   │   └── executor.py
│   ├── models/
│   │   └── schemas.py
│   ├── tools/
│   │   ├── registry.py
│   │   └── schemas.py
│   └── mock_hardware/
│       └── state.py
├── tests/
│   ├── conftest.py
│   ├── test_agent.py
│   └── test_api.py
├── docs/
│   ├── architecture.svg
│   ├── architecture.mmd
│   ├── evaluation-notes.md
│   └── submission-checklist.md
├── .env.example
├── requirements.txt
└── README.md
```

## Local setup

Python 3.11+ is recommended.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Start the API

```powershell
uvicorn app.main:app --reload
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`
- Tool schemas: `http://127.0.0.1:8000/api/v1/tools`
- Mock state: `http://127.0.0.1:8000/api/v1/hardware/state`

## Example requests

### 1. Secure the house

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/agent" `
  -H "Content-Type: application/json" `
  -d '{"command":"I am heading to bed, secure the house."}'
```

### 2. Create an unsafe state

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/hardware/windows/state" `
  -H "Content-Type: application/json" `
  -d '{"window_id":"bedroom","status":"open"}'
```

Then call `/api/v1/agent` again with the security command. The response should show `safety_intervention: true`, and `lock_doors` must be absent from the execution trace.

### 3. Reset the home

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/hardware/reset"
```

### 4. Turn off lights only

```json
{"command":"Please turn off the lights"}
```

The agent checks `get_light_status`, performs `turn_off_lights`, and verifies the final state.

## Optional LLM planner

The default planner is `mock` so the submission is deterministic and works without credentials.

To use an OpenAI-compatible provider, set:

```text
PLANNER_PROVIDER=llm
LLM_BASE_URL=<provider-base-url>
LLM_API_KEY=<secret>
LLM_MODEL=<model-name>
```

The LLM must return a JSON object matching `AgentPlan`. The executor still validates every requested tool and applies the safety policy, so changing the planner does not remove the hardware safety boundary.

## Testing

```powershell
pytest -q
```

The test suite covers:

- successful multi-step security execution
- open-window safety intervention
- prevention of action execution without required status checks
- unsupported intent handling
- lights-only workflow
- health endpoint
- strict tool schema discovery
- agent API integration

## Engineering trade-offs

### Why a deterministic local planner?

It makes the take-home reproducible without depending on an external API, rate limit, or API key. The planner is behind an interface and can be replaced with an LLM without changing the execution boundary.

### Why keep policy outside the LLM?

A language model is probabilistic and should not be the final authority for physical actions. The executor acts as a deterministic trust boundary.

### Why verify after an action?

A tool returning `success=true` is not the same as proving the physical state changed. Re-reading the state allows the agent to detect inconsistent hardware behavior.

## Production evolution

A production implementation could add:

- real IoT/MQTT/device adapters
- OAuth/JWT authentication and per-device authorization
- persistent audit logs and distributed tracing
- idempotency keys and request deduplication
- timeouts, retries and circuit breakers
- human confirmation for high-risk actions
- real ASR/TTS providers
- durable state storage
- richer LLM structured-output/tool-calling support
- policy versioning and automated policy tests

## Submission note

This repository is intentionally a focused proof-of-concept rather than a simulated production cloud deployment. The important evaluation boundary is explicit: **natural language is converted into a structured plan, observations establish physical state, a deterministic policy controls actions, and post-action verification confirms the result.**
