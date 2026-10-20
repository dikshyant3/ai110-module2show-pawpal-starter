# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

The current implementation provides a small, transparent scheduling workflow: register pets, assign timed care tasks, and manage the schedule across those pets.

## What you will build

The app lets an owner add pets and timed tasks, view/filter their schedule, detect exact-time conflicts, and complete one-time or recurring activities.

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

The backend logic lives in `pawpal_system.py`; the final class design is documented in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd).

| Class | Type | Responsibility | Implemented methods |
|-------|------|----------------|---------------------|
| `Task` | dataclass | One care activity: stable ID, description, scheduled time, due date, priority (`Low`/`Medium`/`High`), duration in minutes, frequency (`once`/`daily`/`weekly`), completion status, and the owning pet's name | `mark_complete()`, `next_occurrence()` |
| `Pet` | dataclass | A pet's name, species, and its list of tasks | `add_task()`, `get_task()` |
| `Owner` | dataclass | The owner's name and all registered pets; JSON save/load | `add_pet()`, `get_pet()`, `get_all_tasks()`, `to_json()`, `from_json()`, `save_to_json()`, `load_from_json()` |
| `Scheduler` | class | Plans across all pets by reading tasks through `Owner.get_all_tasks()` | `get_schedule()`, `sort_by_time()`, `filter_tasks()`, `detect_conflicts()`, `find_next_available_slot()`, `complete_task()`, `mark_task_complete()` |

Key design points:

- **Multi-pet support:** `Pet.add_task()` stamps each task with `pet_name`, so tasks combined by `Owner.get_all_tasks()` still show which pet they belong to.
- **Scheduler goes through the Owner:** it never reads a single pet's task list directly.
- **Unique pet names:** `Owner.add_pet()` raises `ValueError` if a pet with the same name is already registered.
- **`get_schedule()` is unsorted:** it returns tasks grouped by pet in the order they were added. Pass the result to `sort_by_time()` for a priority-first plan (see [Smarter Scheduling](#-smarter-scheduling)).

## Features

- **Multi-pet task management:** register pets with distinct names and assign each timed task to one pet.
- **Priority-based scheduling:** `Scheduler.sort_by_time()` orders High before Medium before Low, then orders tasks within each priority by due date and scheduled time.
- **Pet and status filters:** narrow the schedule to one pet, pending tasks, or completed tasks; filters can be combined.
- **Exact-time conflict warnings:** identify pending tasks sharing the same date and time. The Streamlit page names the date, time, pets, and tasks, explains that the warning includes tasks hidden by filters, and prompts the owner to reschedule one of the clashing tasks.
- **Next available time slot:** search from a chosen date and time for the earliest requested-duration opening that does not overlap any pending task. Each task's duration is considered, including openings that move to a later day.
- **Recurring completion:** completing a daily or weekly task creates its next occurrence for the same pet; one-time tasks do not recur.
- **Clear interaction feedback:** forms show validation and success/error messages, while empty states explain how to get started or adjust filters.
- **JSON persistence:** the app automatically loads `data.json` on startup and saves household changes there. Task IDs, dates, times, priorities, durations, recurrence, and completion status are preserved; older saved tasks default to Medium priority and 30 minutes.
- **Session state:** the owner and pet/task data remain available across Streamlit reruns in the active session.

### Save and load household data

The app loads `data.json` from its current working directory when it starts. Adding pets or tasks, completing tasks, and loading an uploaded backup saves the updated household back to that file. The file is created on the first saved change; if it is missing, the app starts with an empty household. Use **Download household JSON** to make a portable backup, or upload a JSON file in **Save or load household data** to restore a household.

```python
owner.save_to_json()  # writes data.json in the current working directory
restored_owner = Owner.load_from_json()  # reads data.json from that directory
```

Pass a path to either method to use a different JSON file. JSON text conversion is also available with `owner.to_json()` and `Owner.from_json(json_text)`. Task IDs, dates and times (in ISO 8601 form), priorities, durations, recurrence, and completion state survive a round trip. Legacy task records without a priority load as `Medium`.

Persistence-related files modified for this feature: `pawpal_system.py` (JSON conversion and file methods), `app.py` (automatic load/save and backup controls), `tests/test_pawpal.py` (round-trip and app persistence coverage), `README.md` (this workflow), and `.gitignore` (keeps the generated household data out of version control). `data.json` is generated at runtime and is not committed.

### Running the demo

`main.py` creates an owner with two pets (Buddy the dog and Luna the cat) and adds five tasks out of time order, two of them at the same time. It then prints the tasks unsorted and sorted, shows the conflict warning, completes a daily task (which adds tomorrow's copy), and prints several filtered views:

```bash
python main.py
```

### Output formatting

The Streamlit schedule uses a compact, column-based task table. Task descriptions get a
care-type emoji (for example, 🚶 for walks, 🍽️ for feeding, and 💊 for medication);
priority labels are color-coded, and task status uses Streamlit's green **✅ Done** and
yellow **⏳ Pending** indicators. Pending rows keep their **Complete** button.

The CLI demo uses the shared helpers in `output_formatting.py`:

- `task_emoji(description)` selects an icon for common task types and uses 🐾 when no
  category matches.
- `task_status(completed)` supplies the consistent done/pending labels used by both
  interfaces.
- `format_task_table(tasks, color=False)` formats task data as an aligned table. The CLI
  enables ANSI green/yellow status text only when stdout is an interactive terminal.

The table uses Python's standard library rather than an added dependency such as
`tabulate`; scheduling, filtering, and completion logic are unchanged.

## 🖥️ Sample Output

Example output from `python main.py` (excerpt):

```
PawPal+ demo for Jordan (Monday, October 19, 2026)

Unsorted (grouped by pet, in the order added)
+------+--------+----------+----------+-------+-----------------+--------+------------+
| Type | Date   | Time     | Priority | Pet   | Task            | Repeat | Status     |
+------+--------+----------+----------+-------+-----------------+--------+------------+
| 🍽️  | Oct 19 | 08:00 AM | Medium   | Buddy | Breakfast       | daily  | ⏳ Pending |
| 🚶   | Oct 19 | 07:30 AM | High     | Buddy | Morning walk    | daily  | ⏳ Pending |
| 🎾   | Oct 19 | 06:15 AM | Low      | Luna  | Play session    | once   | ⏳ Pending |
| 💊   | Oct 19 | 11:00 AM | High     | Luna  | Flea medication | weekly | ⏳ Pending |
| 🍽️  | Oct 19 | 08:00 AM | Medium   | Luna  | Breakfast       | daily  | ⏳ Pending |
+------+--------+----------+----------+-------+-----------------+--------+------------+

Conflicts
------------------------------------------------------------
Conflict on Oct 19 at 08:00 AM — Buddy: Breakfast, Luna: Breakfast

Completed Buddy's Morning walk -> next one added for Oct 20

Filter: Buddy only
Filter: completed
+------+--------+----------+----------+-------+--------------+--------+---------+
| Type | Date   | Time     | Priority | Pet   | Task         | Repeat | Status  |
+------+--------+----------+----------+-------+--------------+--------+---------+
| 🚶   | Oct 19 | 07:30 AM | High     | Buddy | Morning walk | daily  | ✅ Done |
+------+--------+----------+----------+-------+--------------+--------+---------+
```

## 🧪 Testing PawPal+

```bash
python -m pytest
```

The tests in `tests/test_pawpal.py` cover:

- Task completion and recurrence: daily, weekly, and one-time behavior; date rollovers; the next task's due date, time, priority, pet, and pending status.
- Owner and pet behavior: constructor/addition task ownership, task lookup, unknown lookups, duplicate pet names, and collecting tasks.
- JSON persistence: household text and file round trips, preservation of dates, precise times, priorities, recurrence, completion state, pet ownership, and task IDs; legacy task priority defaults and unsupported data versions are checked.
- Scheduling: all-task and date-specific schedules; priority-first ordering by date then time, stable ties, empty inputs, and filters by pet and completion status.
- Next available slot: chained task overlaps, exact interval boundaries, completed tasks, search across midnight, invalid durations, legacy JSON duration defaults, and the Streamlit slot-finder workflow.
- Conflicts: exact matching date/time, multiple conflict slots, conflicts on one pet or across pets, and non-conflicts for different days, one-minute offsets, or completed tasks.
- Completion edge cases: duplicate descriptions and disambiguation by date/time, duplicate completion, identity vs. value-equal tasks, missing pets/tasks, and foreign task objects.
- Streamlit smoke flow and validation: initial empty-pet state, adding a pet and daily task, completing the task to verify the next occurrence appears, checking blank/duplicate submissions show feedback, and confirming conflicts remain visible even when filters hide a clashing task.
- Output formatting: emoji selection, status labels, aligned CLI tables, terminal color control, and the Streamlit task status presentation.

`pytest.ini` sets `pythonpath = .` and `testpaths = tests`. Python syntax was also checked for the backend, Streamlit app, demo, and tests with:

```bash
python -m compileall -q pawpal_system.py app.py main.py tests
```

Latest test run: **50 passed**.

Syntax check result: passed (the command completed successfully and produced no errors). Confidence level: **4/5 stars** based on this test and syntax-check coverage; the tests exercise core backend behavior and a representative UI flow, but are not an exhaustive test of every Streamlit interaction or real browser session.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Orders High, then Medium, then Low; within each priority, orders by due date and scheduled time. Times are stored as `datetime.time`, so no "HH:MM" string parsing is needed. |
| Filtering | `Scheduler.filter_tasks(pet_name, completed)` | Filter by pet, by completion status, or both; leaving a filter out (`None`) means "any". |
| Conflict handling | `Scheduler.detect_conflicts()` | Flags tasks for the same pet or different pets at the **exact** same date and time. Returns warning strings instead of raising; completed tasks are ignored. |
| Next available slot | `Scheduler.find_next_available_slot(start, duration)` | Advances past overlapping pending task intervals using each task's duration. Returns the earliest opening as a `datetime`; the search can roll into later days. |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.complete_task()`, `Scheduler.mark_task_complete()` | Completing a `daily` task adds a new one for the next day (`+ timedelta(days=1)`); `weekly` adds one 7 days later. `once` tasks don't repeat. |

How it works:

- **Sorting:** `get_schedule()` keeps tasks grouped by pet, and `sort_by_time()` orders High, Medium, then Low priority before comparing due date and scheduled time. Thus, a lower-priority task can appear after a later task with higher priority. Equal keys keep their existing order because Python's sort is stable.
- **Filtering:** works across every pet via `Owner.get_all_tasks()`; an unknown pet name returns an empty list rather than an error.
- **Conflict detection:** a lightweight check that groups tasks by `(due_date, scheduled_time)` in one pass and reports any group with two or more tasks. It doesn't look at durations, so 8:00 and 8:15 never clash (see `reflection.md`, section 2b).
- **Next available slot:** treats each pending task as the interval from its scheduled date/time through its duration. When a requested interval intersects a task, the candidate moves to that task's end and checks again, handling chains of overlapping tasks. Completed tasks do not block a slot. Tasks default to 30 minutes; saved households without a duration retain that default.
- **Recurrence:** `complete_task(task)` marks that exact task done and adds the next one to the same pet. `mark_task_complete(pet_name, description)` looks the task up by name first; if the name matches more than one pending task (for example today's and tomorrow's walk), it raises `ValueError` until you also pass `due_date` and/or `scheduled_time`.
- **In the Streamlit app:** owners select Low, Medium, or High priority when adding a task. The Schedule section shows conflict warnings for all tasks, has Pet and Status filters, lists each task's priority in sorted order, and its **Complete** button calls `complete_task()` with the exact task, so recurring tasks add their next copy with the same priority.

## Demo Walkthrough

1. Start the interactive app with `streamlit run app.py`. PawPal+ keeps the owner, pets, and tasks in Streamlit session state across normal page reruns; use the JSON controls near the top of the page to back up or restore a household.
2. In **Pets**, enter a distinct pet name, select its species, and submit **Add pet**. The app confirms successful additions, lists registered pets, and reports blank names or duplicate names.
3. In **Care tasks**, choose the pet, enter a task description, then set its scheduled time, due date, priority (Low, Medium, or High), duration, and repeat interval (`once`, `daily`, or `weekly`). Submit **Add task** to see confirmation and add it to the schedule.
4. In **Care schedule**, use **Find next available slot** to select a starting date/time and requested duration. The app reports the earliest opening after accounting for pending task durations. Review tasks sorted by priority, then date and time; the UI offers pet and status filters (All, Pending, Done), which can be used together. Its empty-state messages distinguish having no tasks from having no tasks matching the selected filters.
5. If pending tasks have the same exact date and time, the app displays a warning with the slot and every conflicting pet/task. Warnings are calculated before filtering, so a filter cannot hide a conflict. Reschedule one of the tasks to remove the clash.
6. Select **Complete** on a pending task. It is marked done; a daily or weekly task adds its next pending occurrence for the same pet, while a one-time task does not recur.

For a deterministic view of the scheduler algorithms, run `python main.py`. Unlike the UI, the CLI demo explicitly requests tasks due today; it prints insertion order and priority-sorted order, reports a conflict, completes a daily task, and prints filtered tables. Its output is shown in [Sample Output](#-sample-output) above. That example puts the 6:15 AM Low-priority task after High- and Medium-priority tasks, demonstrating that priority takes precedence over time.
