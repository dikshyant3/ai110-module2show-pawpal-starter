"""Basic tests for the PawPal+ backend."""

from datetime import date, time, timedelta
from pathlib import Path

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task
from streamlit.testing.v1 import AppTest


def test_task_completion():
    """mark_complete() changes a task's status from pending to completed."""
    task = Task("Morning walk", time(7, 30), date(2026, 10, 18))
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_task_recurrence_rules():
    """Daily and weekly tasks advance by one interval; one-time tasks stop."""
    task = Task("Medication", time(8, 0), date(2026, 12, 31), "daily", pet_name="Buddy")

    daily = task.next_occurrence()
    weekly = Task("Medication", time(8, 0), date(2026, 12, 31), "weekly").next_occurrence()

    assert daily is not None
    assert daily.due_date == date(2027, 1, 1)
    assert daily.scheduled_time == task.scheduled_time
    assert daily.pet_name == task.pet_name
    assert daily.completed is False
    assert weekly is not None
    assert weekly.due_date == date(2027, 1, 7)
    assert Task("Appointment", time(8, 0), date(2026, 12, 31)).next_occurrence() is None


def test_task_addition():
    """add_task() increases the pet's task count and tags the task with the pet's name."""
    pet = Pet("Buddy", "dog")
    assert len(pet.tasks) == 0

    task = Task("Breakfast", time(8, 0), date(2026, 10, 18))
    pet.add_task(task)

    assert len(pet.tasks) == 1
    assert task.pet_name == "Buddy"


def test_pet_constructor_tags_tasks_and_lookup_filters_matches():
    completed = Task("Breakfast", time(8, 0), date(2026, 10, 18), completed=True)
    pending = Task("Breakfast", time(8, 0), date(2026, 10, 19))
    pet = Pet("Buddy", "dog", [completed, pending])

    assert completed.pet_name == "Buddy"
    assert pending.pet_name == "Buddy"
    assert pet.get_task("Breakfast") is pending
    assert pet.get_task("Breakfast", due_date=date(2026, 10, 18)) is None
    assert pet.get_task("Unknown") is None


def test_owner_rejects_duplicate_pet_names_and_returns_all_tasks():
    owner = Owner("Jordan")
    buddy = Pet("Buddy", "dog")
    owner.add_pet(buddy)
    buddy.add_task(Task("Breakfast", time(8, 0), date(2026, 10, 18)))

    with pytest.raises(ValueError, match="already exists"):
        owner.add_pet(Pet("Buddy", "cat"))

    assert owner.get_pet("Missing") is None
    assert owner.get_all_tasks() == buddy.tasks


# --- Scheduling algorithms -------------------------------------------------

DAY = date(2026, 10, 18)


def make_scheduler():
    """Owner with two pets, tasks added out of chronological order."""
    owner = Owner("Jordan")
    buddy = Pet("Buddy", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(buddy)
    owner.add_pet(luna)
    buddy.add_task(Task("Dinner", time(18, 0), DAY, "daily"))
    buddy.add_task(Task("Morning walk", time(7, 30), DAY, "daily"))
    luna.add_task(Task("Flea medication", time(11, 0), DAY, "weekly"))
    luna.add_task(Task("Vet visit", time(9, 0), date(2026, 10, 17)))
    return owner, Scheduler(owner)


def test_get_schedule_returns_all_tasks_or_only_requested_day():
    _, scheduler = make_scheduler()

    assert len(scheduler.get_schedule()) == 4
    assert [task.description for task in scheduler.get_schedule(DAY)] == [
        "Dinner",
        "Morning walk",
        "Flea medication",
    ]
    assert scheduler.get_schedule(date(2026, 10, 20)) == []


def test_sort_by_time_orders_by_date_then_time():
    _, scheduler = make_scheduler()
    ordered = scheduler.sort_by_time(scheduler.get_schedule())
    assert [t.description for t in ordered] == [
        "Vet visit",  # earlier date wins even though its time is later than the walk
        "Morning walk",
        "Flea medication",
        "Dinner",
    ]


def test_sort_by_time_empty_list():
    _, scheduler = make_scheduler()
    assert scheduler.sort_by_time([]) == []


def test_sort_by_time_preserves_order_for_equal_slots():
    owner, scheduler = make_scheduler()
    buddy = owner.get_pet("Buddy")
    buddy.add_task(Task("Second task", time(7, 30), DAY))
    same_slot_tasks = [buddy.tasks[1], buddy.tasks[2]]

    assert scheduler.sort_by_time(same_slot_tasks) == same_slot_tasks


def test_filter_by_pet():
    _, scheduler = make_scheduler()
    assert {t.description for t in scheduler.filter_tasks(pet_name="Luna")} == {
        "Flea medication",
        "Vet visit",
    }


def test_filter_by_status_and_combined():
    owner, scheduler = make_scheduler()
    owner.get_pet("Buddy").tasks[0].mark_complete()  # Dinner
    assert [t.description for t in scheduler.filter_tasks(completed=True)] == ["Dinner"]
    assert len(scheduler.filter_tasks(completed=False)) == 3
    assert [t.description for t in scheduler.filter_tasks("Buddy", False)] == ["Morning walk"]


def test_filter_unknown_pet_returns_empty():
    _, scheduler = make_scheduler()
    assert scheduler.filter_tasks(pet_name="Rex") == []


def test_daily_task_recurs_next_day():
    owner, scheduler = make_scheduler()
    next_task = scheduler.mark_task_complete("Buddy", "Morning walk")

    assert next_task.due_date == date(2026, 10, 19)
    assert next_task.scheduled_time == time(7, 30)
    assert next_task.completed is False
    assert next_task.pet_name == "Buddy"
    assert next_task in owner.get_pet("Buddy").tasks


def test_weekly_task_recurs_next_week():
    _, scheduler = make_scheduler()
    next_task = scheduler.mark_task_complete("Luna", "Flea medication")
    assert next_task.due_date == date(2026, 10, 25)


def test_one_time_task_does_not_recur():
    owner, scheduler = make_scheduler()
    assert scheduler.mark_task_complete("Luna", "Vet visit") is None
    assert len(owner.get_pet("Luna").tasks) == 2


def test_recurrence_crosses_month_boundary():
    task = Task("Pill", time(8, 0), date(2026, 10, 31), "daily")
    assert task.next_occurrence().due_date == date(2026, 11, 1)


def test_completing_twice_raises():
    owner, scheduler = make_scheduler()
    task = owner.get_pet("Luna").tasks[1]
    scheduler.complete_task(task)
    with pytest.raises(ValueError):
        scheduler.complete_task(task)


def test_detect_conflicts_exact_time_across_pets():
    owner, scheduler = make_scheduler()
    owner.get_pet("Luna").add_task(Task("Breakfast", time(7, 30), DAY))
    warnings = scheduler.detect_conflicts(scheduler.get_schedule())
    assert len(warnings) == 1
    assert "Buddy: Morning walk" in warnings[0] and "Luna: Breakfast" in warnings[0]


def test_detect_conflicts_reports_multiple_slots_and_same_pet_tasks():
    owner, scheduler = make_scheduler()
    buddy = owner.get_pet("Buddy")
    buddy.add_task(Task("Second walk", time(7, 30), DAY))
    owner.get_pet("Luna").add_task(Task("Late breakfast", time(18, 0), DAY))

    warnings = scheduler.detect_conflicts(scheduler.get_schedule())

    assert len(warnings) == 2
    assert "Conflict on Oct 18 at 07:30 AM" in warnings[0]
    assert "Conflict on Oct 18 at 06:00 PM" in warnings[1]


def test_detect_conflicts_same_time_different_day_is_not_conflict():
    owner, scheduler = make_scheduler()
    owner.get_pet("Luna").add_task(Task("Breakfast", time(7, 30), date(2026, 10, 19)))
    assert scheduler.detect_conflicts(scheduler.get_schedule()) == []


def test_detect_conflicts_one_minute_apart_is_not_conflict():
    owner, scheduler = make_scheduler()
    owner.get_pet("Luna").add_task(Task("Breakfast", time(7, 31), DAY))
    assert scheduler.detect_conflicts(scheduler.get_schedule()) == []


def test_completed_task_does_not_conflict():
    owner, scheduler = make_scheduler()
    clash = Task("Breakfast", time(7, 30), DAY)
    owner.get_pet("Luna").add_task(clash)
    clash.mark_complete()
    assert scheduler.detect_conflicts(scheduler.get_schedule()) == []


def test_ambiguous_description_raises_until_disambiguated():
    owner, scheduler = make_scheduler()
    buddy = owner.get_pet("Buddy")
    buddy.add_task(Task("Morning walk", time(7, 30), date(2026, 10, 19), "daily"))

    with pytest.raises(ValueError, match="2 incomplete tasks"):
        scheduler.mark_task_complete("Buddy", "Morning walk")
    assert not any(t.completed for t in buddy.tasks)  # nothing was changed

    scheduler.mark_task_complete("Buddy", "Morning walk", due_date=date(2026, 10, 19))
    done = [t for t in buddy.tasks if t.completed]
    assert len(done) == 1 and done[0].due_date == date(2026, 10, 19)


def test_ambiguous_description_can_be_resolved_by_time():
    owner, scheduler = make_scheduler()
    buddy = owner.get_pet("Buddy")
    buddy.add_task(Task("Morning walk", time(9, 0), DAY))

    scheduler.mark_task_complete("Buddy", "Morning walk", scheduled_time=time(9, 0))

    assert buddy.get_task("Morning walk", scheduled_time=time(7, 30)) is not None
    assert buddy.get_task("Morning walk", scheduled_time=time(9, 0)) is None


def test_complete_task_uses_identity_not_equality():
    """Two value-identical tasks: completing one object must not touch the other."""
    owner, scheduler = make_scheduler()
    buddy = owner.get_pet("Buddy")
    twin_a = Task("Brush", time(20, 0), DAY)
    twin_b = Task("Brush", time(20, 0), DAY)
    buddy.add_task(twin_a)
    buddy.add_task(twin_b)

    scheduler.complete_task(twin_b)
    assert twin_b.completed and not twin_a.completed


def test_complete_task_rejects_foreign_task():
    _, scheduler = make_scheduler()
    stray = Task("Dinner", time(18, 0), DAY, "daily", pet_name="Buddy")  # never added
    with pytest.raises(ValueError):
        scheduler.complete_task(stray)


def test_mark_task_complete_unknown_pet_or_task():
    _, scheduler = make_scheduler()
    with pytest.raises(ValueError):
        scheduler.mark_task_complete("Rex", "Dinner")
    with pytest.raises(ValueError):
        scheduler.mark_task_complete("Buddy", "Swim")


def test_complete_task_rejects_task_owned_by_another_pet():
    owner, scheduler = make_scheduler()
    foreign_owner = Owner("Taylor")
    foreign_pet = Pet("Buddy", "dog")
    foreign_owner.add_pet(foreign_pet)
    task = Task("Walk", time(7, 0), DAY, pet_name="Buddy")
    foreign_pet.add_task(task)

    with pytest.raises(ValueError, match="does not belong"):
        scheduler.complete_task(task)

    assert task.completed is False


def test_streamlit_add_task_and_complete_flow():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()
    assert not app.exception
    assert any(message.value.startswith("No pets added yet.") for message in app.info)

    app.text_input[1].set_value("Buddy")
    app.button[0].click().run()
    assert not app.exception
    assert any(message.value == "Added Buddy the dog." for message in app.success)

    app.text_input[2].set_value("Breakfast")
    next(item for item in app.selectbox if item.label == "Repeat").select("daily")
    app.button(key="FormSubmitter:add_task_form-Add task").click().run()
    assert not app.exception
    assert any(message.value == "Added 'Breakfast' for Buddy." for message in app.success)
    assert any(button.label == "Complete" for button in app.button)

    due_date = app.date_input[0].value
    app.button[-1].click().run()
    assert not app.exception
    assert any(message.value == "Done" for message in app.success)
    next_date = due_date + timedelta(days=1)
    assert any(next_date.strftime("%b %d") in item.value for item in app.caption)


def test_streamlit_validation_and_duplicate_pet_feedback():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()

    app.button[0].click().run()
    assert any("Please enter a pet name." == message.value for message in app.warning)

    app.text_input[1].set_value("Buddy")
    app.button[0].click().run()
    app.text_input[1].set_value("Buddy")
    app.button[0].click().run()
    assert any("already exists" in message.value for message in app.error)

    app.text_input[2].set_value(" ")
    app.button(key="FormSubmitter:add_task_form-Add task").click().run()
    assert any("Please enter a task description." == message.value for message in app.warning)
