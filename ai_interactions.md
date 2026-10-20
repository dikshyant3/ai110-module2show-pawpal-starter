# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Implement a Scheduler algorithm that finds the earliest available time interval
for a requested duration, based on existing tasks and their durations. Integrate
it into Streamlit, add pytest coverage, preserve existing behavior, run all tests,
and document this workflow.

**What did the agent do?**

Added a default 30-minute duration to tasks, retained that duration for recurring
tasks, and included it in JSON serialization while keeping old saved households
loadable. Implemented interval-based next-slot search across pets and dates,
including chained overlaps and tasks crossing midnight. Added task-duration
inputs and the slot finder to Streamlit. Updated the UML and README, and added
tests for interval boundaries, completed tasks, chained overlaps, midnight
searches, invalid durations, legacy JSON, and the Streamlit workflow.

Files modified: `pawpal_system.py`, `app.py`, `tests/test_pawpal.py`,
`diagrams/uml_final.mmd`, `README.md`, and `ai_interactions.md`.
Validation: `.venv/bin/pytest -q` (44 passed) and
`.venv/bin/python -m compileall -q pawpal_system.py app.py main.py tests`.

**What did you have to verify or fix manually?**

The first test run exposed a test-fixture setup mistake: its pet had not been
registered with the owner. I added the missing registration, reran the complete
suite successfully, and verified the compile check. No application behavior
needed a manual correction.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

### Model / tool used

- **Option A:** ChatGPT (GPT-6 Instant).
- **Option B:** Claude (Opus 5.5 Medium).

### Prompt / task

Both responses address this task: suggest a weekly recurring-task rescheduling
algorithm using the existing `Task` and `Scheduler` architecture; explain it,
provide Python code, and discuss duplicate completion, date changes, and
preserving task attributes.

### Useful aspects of each response

- **Option A — ChatGPT:** Recommends advancing from the original scheduled due
  date by seven days, rather than from the completion date, to maintain a
  consistent weekly schedule. It calls out duplicate completion and duplicate
  occurrences on the next date, and identifies the attributes a new occurrence
  should retain while receiving a new ID and pending status. It also notes that
  Python date arithmetic handles month, leap-year, and year boundaries.
- **Option B — Claude:** Separates duplicate-completion protection from
  duplicate-occurrence protection, and describes an explicit series identifier
  and `(series_id, due_date)` lookup. It discusses late completion, end dates,
  daylight-saving considerations, and the tradeoff between scanning tasks and
  maintaining an index. It proposes `dataclasses.replace()` to carry forward
  fields when making a new occurrence.

### Flaws or limitations

- **Option A — ChatGPT:** The response is a prose summary, not the requested
  Python code. It does not explain how recurring-series identity is represented
  or how to resolve an already-existing occurrence beyond saying to check for
  one.
- **Option B — Claude:** The response describes a separate `pawpal_scheduler.py`
  module and fields such as `series_id`, `end_date`, `completed_on`, and
  `next_task_id`, while warning that its field names are guesses. Those fields
  and that module are not part of this project's existing `Task` architecture.
  It says a built-in self-test passed, but does not include the promised file or
  code here, so that claim cannot be assessed from the response alone.

### Final implementation decision

Keep the existing class design: `Task.next_occurrence()` advances a weekly
task's `due_date` by seven days and creates a fresh `Task`, retaining its
description, scheduled time, frequency, pet name, duration, and priority; the
new task defaults to a new ID and incomplete status. `Scheduler.complete_task()`
validates ownership and rejects completing an already-completed task before
adding the next occurrence. This uses the scheduled due date as the recurrence
anchor, consistent with Option A and the useful date/attribute guidance from
both responses. The project does not add series IDs or deduplicate an occurrence
that was independently created for the same series and date.
