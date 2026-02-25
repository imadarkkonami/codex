# Agentic AI System Blueprint (Actionable)

This is an implementation-focused blueprint to help you go from "idea" to a working **agentic AI system** with clear milestones, interfaces, and guardrails.

## 1) Pick one narrow use case (first)

Do not start with a general-purpose agent. Start with one workflow that has:

- clear input (`goal`, `constraints`, `context`)
- measurable output (artifact, decision, API side effect)
- known tools (3-5 max)
- clear failure handling (retry, escalate, abort)

### Example MVP use cases

- Support triage agent (classify + suggest response + draft ticket updates)
- Sales research agent (enrich account + summarize signals + create CRM note)
- Internal coding helper (read repo + propose patch + run tests)

## 2) MVP architecture you can ship in 2 weeks

```text
Client/API
   |
   v
Orchestrator -----> Policy Guard
   |                    |
   v                    v
Planner ----------> Tool Gateway
   |                    |
   v                    v
Executor ---------> Memory Store
   |
   v
Evaluator/Critic
```

### Core components

1. **Orchestrator**
   - Creates `run_id`, enforces budget/deadline.
   - Stores run state transitions.

2. **Planner**
   - Converts goal into ordered steps with tool candidates.
   - Emits strict schema (JSON).

3. **Executor**
   - Executes one step at a time.
   - Calls tool gateway only (never raw tools directly).

4. **Tool Gateway**
   - Validation + authz + timeout + retries.
   - Central point for audit logs.

5. **Memory Store**
   - `run_memory` (ephemeral)
   - `long_term_memory` (facts, preferences, prior outcomes)

6. **Evaluator/Critic**
   - Step-level checks and final acceptance checks.
   - Triggers replan/human escalation.

7. **Policy Guard**
   - Prompt injection filters.
   - Data sensitivity checks.
   - "High-risk action" approval gate.

## 3) Canonical run state machine

Use explicit states so the system is debuggable and replayable.

- `RECEIVED`
- `PLANNED`
- `EXECUTING_STEP`
- `VERIFYING_STEP`
- `REPLANNING`
- `AWAITING_HUMAN_APPROVAL`
- `COMPLETED`
- `FAILED`
- `CANCELLED`

A run is invalid if it transitions outside this state graph.

## 4) Data contracts (copy this shape)

### 4.1 Task input

```json
{
  "goal": "Generate a weekly support risk report",
  "constraints": {
    "max_cost_usd": 1.5,
    "deadline_seconds": 120,
    "allowed_tools": ["ticket.search", "ticket.update", "slack.post"]
  },
  "context": {
    "tenant_id": "acme",
    "requester_id": "u_123",
    "priority": "high"
  }
}
```

### 4.2 Planner output

```json
{
  "plan_id": "pln_001",
  "steps": [
    {
      "step_id": "s1",
      "description": "Fetch unresolved P1/P2 tickets",
      "tool": "ticket.search",
      "input": {"severity": ["P1", "P2"], "status": "open"},
      "verification": "result.count >= 0"
    }
  ]
}
```

### 4.3 Tool contract

```json
{
  "tool_name": "ticket.search",
  "request_schema": {"type": "object"},
  "response_schema": {"type": "object"},
  "timeout_ms": 8000,
  "retry_policy": {"max_retries": 2, "backoff_ms": 200}
}
```

## 5) Minimal reliable agent loop

Run this loop with strict limits:

1. Plan from goal.
2. For each step:
   - validate step + tool permissions
   - execute tool/model call
   - verify output
   - persist trace
3. Replan on failed verification (max 2 replans).
4. Escalate to human for blocked/high-risk actions.
5. End with `COMPLETED` or `FAILED`.

### Hard limits (recommended defaults)

- max steps: 8
- max replans: 2
- max runtime: 180 seconds
- max tool failures before fail-fast: 3

## 6) Tooling and safety baseline (non-negotiable)

- Tool allowlist per tenant and per run.
- JSON schema validation for every tool call.
- Redaction for secrets/PII before log write.
- Idempotency key for write operations.
- Approval workflow for destructive actions.
- Immutable audit log (`run_id`, `step_id`, tool input/output hashes).

## 7) Memory model that avoids chaos

Split memory into three stores:

1. **Working memory** (in-run scratchpad)
   - short-lived summaries and interim outputs.

2. **Episodic memory** (run outcomes)
   - what was attempted, what worked, what failed.

3. **Semantic memory** (stable facts)
   - preferences, policies, entity facts with provenance.

### Write policy

- automatic write: non-sensitive, high-confidence facts
- gated write: user preferences and policy-sensitive content
- denied write: credentials/secrets/raw tokens

## 8) Evaluation harness (start before scale)

Track four categories:

- **Task quality**: correctness/completeness rubric score
- **Safety**: policy violations and blocked risky actions
- **Reliability**: success rate, retries, timeout rate
- **Economics**: p50/p95 latency, cost per successful run

### CI regression gate

Fail CI if any of the following regress > threshold:

- quality score drops > 3%
- cost/run increases > 15%
- p95 latency increases > 20%
- policy violation rate increases > 0%

## 9) Suggested repo layout

```text
agent-system/
  app/
    api/
    orchestrator/
    planner/
    executor/
    tools/
    policy/
    memory/
    evals/
    observability/
  tests/
    unit/
    integration/
    eval_regression/
  configs/
    prompts/
    policies/
    tools/
```

## 10) First implementation milestones

### Milestone A (Days 1-3)

- Stand up orchestrator API + run state persistence.
- Build one planner prompt and strict JSON parser.
- Implement two read-only tools.

### Milestone B (Days 4-7)

- Add executor with step verification.
- Add evaluator and replan logic.
- Add tracing + cost/latency metrics.

### Milestone C (Days 8-14)

- Add memory write policies.
- Add approval flow for risky actions.
- Add 20-50 regression eval tasks and CI gate.

## 11) Common pitfalls and direct fixes

- **Overly broad tool access** -> enforce per-run allowlists.
- **Unbounded loops** -> state machine + max step/replan limits.
- **Unreproducible failures** -> structured traces + replay endpoint.
- **Prompt drift** -> prompt versioning + eval gates on every change.
- **Poor ROI** -> route simple tasks to cheaper models and cache retrieval.

## 12) Practical tech stack (example)

- Backend: Python + FastAPI
- Queue/workflow: Temporal (or Celery/Redis for simpler stack)
- Storage: Postgres + Redis + vector DB
- Model access: gateway with routing/fallback
- Observability: OpenTelemetry + Grafana/Datadog

## 13) Definition of done for MVP

You have a real MVP only when all are true:

- [ ] Agent completes target workflow end-to-end with no manual edits in >=70% of runs.
- [ ] Every tool call is schema-validated and audit logged.
- [ ] High-risk actions require human approval.
- [ ] Replay/debug works for any failed run.
- [ ] Eval suite runs in CI and blocks regressions.

---

If you want, the next step is to create a **use-case-specific implementation plan** (API contracts, tables, prompts, and week-by-week task breakdown) for your exact domain.
