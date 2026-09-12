# Evaluation Notes

## What the evaluator should notice

1. **Agentic behavior:** the command is translated into a multi-step plan rather than a single hard-coded API call.
2. **State awareness:** status tools inspect the current simulated physical environment before actions.
3. **Safety boundary:** the executor independently blocks unsafe actions; the planner cannot bypass this rule.
4. **Strict contracts:** every tool input/output is represented by Pydantic models with extra fields rejected.
5. **Verification:** the agent checks the resulting state after actions.
6. **Provider independence:** the default local planner is deterministic, while an optional OpenAI-compatible planner is available behind the same interface.
7. **Observability:** each tool result contains category, success/error, and execution duration.

## Suggested five-minute demo

1. Open `/docs`.
2. Reset the mock home.
3. Execute `I'm heading to bed, secure the house.`
4. Expand the response and show the ordered tool trace.
5. Open the bedroom window using `/api/v1/hardware/windows/state`.
6. Repeat the security command.
7. Show that the status check detects the open window and the action tools are not executed.
8. Reset the home and run `Please turn off the lights` to demonstrate a second intent.

## Interview talking points

- The LLM/planner is not trusted with direct hardware access.
- Tool schemas make the agent/tool boundary explicit and machine-validatable.
- The policy layer is deterministic and testable.
- Status-before-action is enforced by the executor rather than by prompt instructions alone.
- Verification is part of the agent loop, not an afterthought.
