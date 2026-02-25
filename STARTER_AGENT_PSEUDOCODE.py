"""Minimal reference pseudocode for an agentic system loop.

This file is intentionally lightweight and framework-agnostic so it can be
adapted to FastAPI/Node/Temporal/etc.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RunState(str, Enum):
    RECEIVED = "RECEIVED"
    PLANNED = "PLANNED"
    EXECUTING_STEP = "EXECUTING_STEP"
    VERIFYING_STEP = "VERIFYING_STEP"
    REPLANNING = "REPLANNING"
    AWAITING_HUMAN_APPROVAL = "AWAITING_HUMAN_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class Step:
    step_id: str
    description: str
    tool: str
    tool_input: dict[str, Any]
    verification_rule: str


@dataclass
class Plan:
    plan_id: str
    steps: list[Step]


@dataclass
class RunContext:
    run_id: str
    goal: str
    allowed_tools: set[str]
    max_steps: int = 8
    max_replans: int = 2
    state: RunState = RunState.RECEIVED
    trace: list[dict[str, Any]] = field(default_factory=list)


def create_plan(goal: str) -> Plan:
    # Replace with LLM planner call + strict JSON parsing.
    return Plan(
        plan_id="pln_demo",
        steps=[
            Step(
                step_id="s1",
                description="Collect required context",
                tool="context.fetch",
                tool_input={"goal": goal},
                verification_rule="result is not None",
            )
        ],
    )


def call_tool(tool: str, payload: dict[str, Any]) -> dict[str, Any]:
    # Replace with tool gateway call (authz, validation, timeout, retries).
    return {"ok": True, "result": payload}


def verify_step(_rule: str, output: dict[str, Any]) -> bool:
    # Replace with deterministic checks and/or evaluator model.
    return bool(output.get("ok"))


def run_agent(ctx: RunContext) -> RunContext:
    replans = 0

    while ctx.state not in {RunState.COMPLETED, RunState.FAILED}:
        if ctx.state == RunState.RECEIVED:
            plan = create_plan(ctx.goal)
            ctx.trace.append({"event": "plan_created", "plan_id": plan.plan_id})
            ctx.state = RunState.PLANNED
            step_index = 0

        elif ctx.state == RunState.PLANNED:
            if step_index >= len(plan.steps):
                ctx.state = RunState.COMPLETED
                continue
            ctx.state = RunState.EXECUTING_STEP

        elif ctx.state == RunState.EXECUTING_STEP:
            step = plan.steps[step_index]
            if step.tool not in ctx.allowed_tools:
                ctx.trace.append({"event": "tool_denied", "tool": step.tool})
                ctx.state = RunState.FAILED
                continue

            result = call_tool(step.tool, step.tool_input)
            ctx.trace.append(
                {
                    "event": "tool_called",
                    "step_id": step.step_id,
                    "tool": step.tool,
                    "result": result,
                }
            )
            last_result = result
            ctx.state = RunState.VERIFYING_STEP

        elif ctx.state == RunState.VERIFYING_STEP:
            step = plan.steps[step_index]
            if verify_step(step.verification_rule, last_result):
                step_index += 1
                ctx.state = RunState.PLANNED
            elif replans < ctx.max_replans:
                replans += 1
                ctx.state = RunState.REPLANNING
            else:
                ctx.state = RunState.FAILED

        elif ctx.state == RunState.REPLANNING:
            plan = create_plan(ctx.goal)
            step_index = 0
            ctx.trace.append({"event": "replanned", "plan_id": plan.plan_id})
            ctx.state = RunState.PLANNED

    return ctx


if __name__ == "__main__":
    context = RunContext(
        run_id="run_demo",
        goal="Generate an incident summary",
        allowed_tools={"context.fetch"},
    )
    final = run_agent(context)
    print(final.state)
    print(final.trace)
