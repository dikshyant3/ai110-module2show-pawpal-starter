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
| `Task` | dataclass | One care activity: description, scheduled time, due date, frequency (`once`/`daily`/`weekly`), completion status, and the owning pet's name | `mark_complete()` |
| `Pet` | dataclass | A pet's name, species, and its list of tasks | `add_task()`, `get_task()` |
| `Owner` | dataclass | The owner's name and all registered pets | `add_pet()`, `get_pet()`, `get_all_tasks()` |
| `Scheduler` | class | Plans across all pets by reading tasks through `Owner.get_all_tasks()` | `get_schedule()` |

Key design points:

- **Multi-pet support:** `Pet.add_task()` stamps each task with `pet_name`, so tasks combined by `Owner.get_all_tasks()` still show which pet they belong to.
- **Scheduler goes through the Owner:** it never reads a single pet's task list directly.
- **Unique pet names:** `Owner.add_pet()` raises `ValueError` if a pet with the same name is already registered.
- **Not yet implemented (Phase 4):** `sort_by_time()`, `filter_tasks()`, `detect_conflicts()`, `mark_task_complete()`, and `Task.next_occurrence()`. Until sorting is added, `get_schedule()` returns tasks grouped by pet in the order they were added.

### Running the demo

`main.py` creates an owner with two pets (Buddy the dog and Luna the cat), registers four tasks, marks one complete, and prints today's schedule:

```bash
python main.py
```

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

Output of `python main.py`:

```
Today's Schedule for Jordan (Sunday, October 18, 2026)
--------------------------------------------------
07:30 AM  Buddy   Morning walk      [Done]
08:00 AM  Buddy   Breakfast         [Pending]
12:00 PM  Luna    Flea medication   [Pending]
06:15 PM  Luna    Play session      [Pending]
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage (requires: pip install pytest-cov):
pytest --cov
```

Current tests in `tests/test_pawpal.py`:

- `test_task_completion`: `mark_complete()` changes a task's status from pending to completed.
- `test_task_addition`: `add_task()` adds the task to the pet's list and sets its `pet_name`.

`pytest.ini` sets `pythonpath = .` so plain `pytest` can import `pawpal_system` from the project root, and `testpaths = tests` points pytest at the `tests/` folder.

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.13, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/dikshyant/codepath-ai110/Labs/ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 2 items

tests/test_pawpal.py ..                                                  [100%]

============================== 2 passed in 0.01s ===============================
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
