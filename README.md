# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## ⚙️ Core Implementation

The backend logic lives in `pawpal_system.py` and follows the design in `diagrams/uml_draft.mmd`.

| Class | Type | Responsibility | Implemented methods |
|-------|------|----------------|---------------------|
| `Task` | dataclass | One care activity: description, scheduled time, due date, frequency (`once`/`daily`/`weekly`), completion status, and the owning pet's name | `mark_complete()`, `next_occurrence()` |
| `Pet` | dataclass | A pet's name, species, and its list of tasks | `add_task()`, `get_task()` |
| `Owner` | dataclass | The owner's name and all registered pets | `add_pet()`, `get_pet()`, `get_all_tasks()` |
| `Scheduler` | class | Plans across all pets by reading tasks through `Owner.get_all_tasks()` | `get_schedule()`, `sort_by_time()`, `filter_tasks()`, `detect_conflicts()`, `complete_task()`, `mark_task_complete()` |

Key design points:

- **Multi-pet support:** `Pet.add_task()` stamps each task with `pet_name`, so tasks combined by `Owner.get_all_tasks()` still show which pet they belong to.
- **Scheduler goes through the Owner:** it never reads a single pet's task list directly.
- **Unique pet names:** `Owner.add_pet()` raises `ValueError` if a pet with the same name is already registered.
- **`get_schedule()` is unsorted:** it returns tasks grouped by pet in the order they were added. Pass the result to `sort_by_time()` for a chronological plan (see [Smarter Scheduling](#-smarter-scheduling)).

### Running the demo

`main.py` creates an owner with two pets (Buddy the dog and Luna the cat) and adds five tasks out of time order, two of them at the same time. It then prints the tasks unsorted and sorted, shows the conflict warning, completes a daily task (which adds tomorrow's copy), and prints several filtered views:

```bash
python main.py
```

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

Output of `python main.py`:

```
PawPal+ demo for Jordan (Monday, October 19, 2026)

Unsorted (grouped by pet, in the order added)
------------------------------------------------------------
Oct 19  08:00 AM  Buddy   Breakfast         daily   [Pending]
Oct 19  07:30 AM  Buddy   Morning walk      daily   [Pending]
Oct 19  06:15 PM  Luna    Play session      once    [Pending]
Oct 19  11:00 AM  Luna    Flea medication   weekly  [Pending]
Oct 19  08:00 AM  Luna    Breakfast         daily   [Pending]

Sorted by time
------------------------------------------------------------
Oct 19  07:30 AM  Buddy   Morning walk      daily   [Pending]
Oct 19  08:00 AM  Buddy   Breakfast         daily   [Pending]
Oct 19  08:00 AM  Luna    Breakfast         daily   [Pending]
Oct 19  11:00 AM  Luna    Flea medication   weekly  [Pending]
Oct 19  06:15 PM  Luna    Play session      once    [Pending]

Conflicts
------------------------------------------------------------
Conflict on Oct 19 at 08:00 AM — Buddy: Breakfast, Luna: Breakfast

Completed Buddy's Morning walk -> next one added for Oct 20

Filter: Buddy only
------------------------------------------------------------
Oct 19  07:30 AM  Buddy   Morning walk      daily   [Done]
Oct 19  08:00 AM  Buddy   Breakfast         daily   [Pending]
Oct 20  07:30 AM  Buddy   Morning walk      daily   [Pending]

Filter: completed
------------------------------------------------------------
Oct 19  07:30 AM  Buddy   Morning walk      daily   [Done]

Filter: Luna, pending
------------------------------------------------------------
Oct 19  08:00 AM  Luna    Breakfast         daily   [Pending]
Oct 19  11:00 AM  Luna    Flea medication   weekly  [Pending]
Oct 19  06:15 PM  Luna    Play session      once    [Pending]
```

## 🧪 Testing PawPal+

```bash
python -m pytest
```

The 29 tests in `tests/test_pawpal.py` cover:

- Task completion and recurrence: daily, weekly, and one-time behavior; date rollovers; the next task's due date, time, pet, and pending status.
- Owner and pet behavior: constructor/addition task ownership, task lookup, unknown lookups, duplicate pet names, and collecting tasks.
- Scheduling: all-task and date-specific schedules; chronological ordering by date then time, stable ties, empty inputs, and filters by pet and completion status.
- Conflicts: exact matching date/time, multiple conflict slots, conflicts on one pet or across pets, and non-conflicts for different days, one-minute offsets, or completed tasks.
- Completion edge cases: duplicate descriptions and disambiguation by date/time, duplicate completion, identity vs. value-equal tasks, missing pets/tasks, and foreign task objects.
- Streamlit smoke flow: initial empty-pet state, adding a pet and daily task, and completing the task to verify the next occurrence appears.

`pytest.ini` sets `pythonpath = .` and `testpaths = tests`. Python syntax was also checked for the backend, Streamlit app, demo, and tests with:

```bash
python -m compileall -q pawpal_system.py app.py main.py tests
```

Actual test output:

```
============================= test session starts ==============================
(.venv) dikshyant@Mac ai110-module2show-pawpal-starter % python -m pytest
============================== test session starts ===============================
platform darwin -- Python 3.13.13, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/dikshyant/codepath-ai110/Labs/ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 29 items                                                               

tests/test_pawpal.py .............................                         [100%]

=============================== 29 passed in 0.74s ===============================
```

Syntax check result: passed (the command completed successfully and produced no errors). Confidence level: **4/5 stars** based on this test and syntax-check coverage; the tests exercise core backend behavior and a representative UI flow, but are not an exhaustive test of every Streamlit interaction or real browser session.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Orders by due date, then scheduled time, using `sorted()` with a `(due_date, scheduled_time)` key. Times are stored as `datetime.time`, so no "HH:MM" string parsing is needed. |
| Filtering | `Scheduler.filter_tasks(pet_name, completed)` | Filter by pet, by completion status, or both; leaving a filter out (`None`) means "any". |
| Conflict handling | `Scheduler.detect_conflicts()` | Flags tasks for the same pet or different pets at the **exact** same date and time. Returns warning strings instead of raising; completed tasks are ignored. |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.complete_task()`, `Scheduler.mark_task_complete()` | Completing a `daily` task adds a new one for the next day (`+ timedelta(days=1)`); `weekly` adds one 7 days later. `once` tasks don't repeat. |

How it works:

- **Sorting:** `get_schedule()` keeps tasks grouped by pet, and `sort_by_time()` turns that into one timeline. Ties keep their existing order because Python's sort is stable.
- **Filtering:** works across every pet via `Owner.get_all_tasks()`; an unknown pet name returns an empty list rather than an error.
- **Conflict detection:** a lightweight check that groups tasks by `(due_date, scheduled_time)` in one pass and reports any group with two or more tasks. It doesn't look at durations, so 8:00 and 8:15 never clash (see `reflection.md`, section 2b).
- **Recurrence:** `complete_task(task)` marks that exact task done and adds the next one to the same pet. `mark_task_complete(pet_name, description)` looks the task up by name first; if the name matches more than one pending task (for example today's and tomorrow's walk), it raises `ValueError` until you also pass `due_date` and/or `scheduled_time`.
- **In the Streamlit app:** the Schedule section shows conflict warnings for all tasks, has Pet and Status filters, lists tasks in sorted order, and its **Complete** button calls `complete_task()` with the exact task, so recurring tasks add their next copy.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
