"""Basic tests for the PawPal+ backend."""

from datetime import date, time

from pawpal_system import Pet, Task


def test_task_completion():
    """mark_complete() changes a task's status from pending to completed."""
    task = Task("Morning walk", time(7, 30), date(2026, 10, 18))
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_task_addition():
    """add_task() increases the pet's task count and tags the task with the pet's name."""
    pet = Pet("Buddy", "dog")
    assert len(pet.tasks) == 0

    task = Task("Breakfast", time(8, 0), date(2026, 10, 18))
    pet.add_task(task)

    assert len(pet.tasks) == 1
    assert task.pet_name == "Buddy"


# --- Scheduling algorithms -------------------------------------------------

import pytest

from pawpal_system import Owner, Scheduler

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
