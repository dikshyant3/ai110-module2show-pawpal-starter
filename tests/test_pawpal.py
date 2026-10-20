"""Basic tests for the PawPal+ backend."""

from datetime import date, datetime, time, timedelta
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


def test_task_duration_must_be_positive_whole_minutes():
    for invalid_duration in (0, -5, 1.5, True):
        with pytest.raises(ValueError, match="positive whole number"):
            Task("Walk", time(7, 30), DAY, duration_minutes=invalid_duration)


def test_task_priority_defaults_to_medium_and_rejects_invalid_values():
    assert Task("Walk", time(7, 30), DAY).priority == "Medium"
    for invalid_priority in ("urgent", "", None, 1):
        with pytest.raises(ValueError, match="Low, Medium, or High"):
            Task("Walk", time(7, 30), DAY, priority=invalid_priority)


def test_task_recurrence_rules():
    """Daily and weekly tasks advance by one interval; one-time tasks stop."""
    task = Task(
        "Medication",
        time(8, 0),
        date(2026, 12, 31),
        "daily",
        pet_name="Buddy",
        priority="High",
    )

    daily = task.next_occurrence()
    weekly = Task("Medication", time(8, 0), date(2026, 12, 31), "weekly").next_occurrence()

    assert daily is not None
    assert daily.due_date == date(2027, 1, 1)
    assert daily.scheduled_time == task.scheduled_time
    assert daily.pet_name == task.pet_name
    assert daily.completed is False
    assert daily.duration_minutes == task.duration_minutes
    assert daily.priority == "High"
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


def test_owner_json_round_trip_preserves_task_data_and_identity():
    owner = Owner("Jordan")
    buddy = Pet("Buddy", "dog")
    owner.add_pet(buddy)
    completed = Task(
        "Medication",
        time(8, 15, 30, 123456),
        date(2026, 10, 18),
        "daily",
        completed=True,
    )
    twin_a = Task("Brush", time(20, 0), date(2026, 10, 18))
    twin_b = Task("Brush", time(20, 0), date(2026, 10, 18))
    weekly = Task(
        "Bath",
        time(10, 45),
        date(2026, 10, 19),
        "weekly",
        duration_minutes=45,
        priority="Low",
    )
    for task in (completed, twin_a, twin_b, weekly):
        buddy.add_task(task)

    restored = Owner.from_json(owner.to_json())

    assert restored.name == owner.name
    restored_buddy = restored.get_pet("Buddy")
    assert restored_buddy.species == "dog"
    assert [task.task_id for task in restored_buddy.tasks] == [
        task.task_id for task in buddy.tasks
    ]
    restored_completed, restored_twin_a, restored_twin_b, restored_weekly = (
        restored_buddy.tasks
    )
    assert restored_completed.scheduled_time == time(8, 15, 30, 123456)
    assert restored_completed.due_date == date(2026, 10, 18)
    assert restored_completed.frequency == "daily"
    assert restored_completed.completed is True
    assert restored_completed.pet_name == "Buddy"
    assert restored_completed.duration_minutes == 30
    assert restored_weekly.duration_minutes == 45
    assert restored_completed.priority == "Medium"
    assert restored_weekly.priority == "Low"
    assert restored_twin_a.task_id != restored_twin_b.task_id
    assert restored_twin_a == restored_twin_b

    next_task = Scheduler(restored).complete_task(restored_weekly)
    assert restored_weekly.completed is True
    assert next_task.due_date == date(2026, 10, 26)
    assert next_task.frequency == "weekly"
    assert next_task.completed is False
    assert next_task.pet_name == "Buddy"
    assert next_task.priority == "Low"
    assert next_task.task_id not in {task.task_id for task in restored_buddy.tasks[:-1]}


def test_owner_save_and_load_json_file(tmp_path):
    owner = Owner("Jordan")
    owner.add_pet(Pet("Buddy", "dog"))
    path = tmp_path / "data.json"

    owner.save_to_json(path)

    assert Owner.load_from_json(path).to_dict() == owner.to_dict()


def test_owner_save_and_load_json_default_to_data_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    owner = Owner("Jordan")
    owner.add_pet(Pet("Buddy", "dog"))

    owner.save_to_json()

    assert (tmp_path / "data.json").is_file()
    assert Owner.load_from_json().to_dict() == owner.to_dict()


def test_owner_rejects_unsupported_json_version():
    with pytest.raises(ValueError, match="Unsupported or invalid"):
        Owner.from_json('{"version": 2, "owner": {"name": "Jordan", "pets": []}}')


def test_owner_loads_legacy_json_with_default_task_duration():
    owner = Owner("Jordan")
    pet = Pet("Buddy", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", time(7, 30), date(2026, 10, 18)))
    legacy_data = owner.to_dict()
    del legacy_data["owner"]["pets"][0]["tasks"][0]["duration_minutes"]
    del legacy_data["owner"]["pets"][0]["tasks"][0]["priority"]

    restored = Owner.from_dict(legacy_data)

    assert restored.get_pet("Buddy").tasks[0].duration_minutes == 30
    assert restored.get_pet("Buddy").tasks[0].priority == "Medium"


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


def test_sort_by_time_orders_by_priority_then_date_then_time():
    _, scheduler = make_scheduler()
    pet = scheduler.owner.get_pet("Buddy")
    pet.add_task(Task("High later", time(10, 0), DAY, priority="High"))
    pet.add_task(Task("Low early", time(6, 0), DAY, priority="Low"))
    pet.add_task(
        Task("High next day", time(7, 0), DAY + timedelta(days=1), priority="High")
    )
    ordered = scheduler.sort_by_time(scheduler.get_schedule())
    assert [t.description for t in ordered] == [
        "High later",
        "High next day",
        "Vet visit",
        "Morning walk",
        "Flea medication",
        "Dinner",
        "Low early",
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


def test_sort_by_time_preserves_input_order_for_equal_priority_date_and_time():
    owner, scheduler = make_scheduler()
    buddy = owner.get_pet("Buddy")
    first = Task("First", time(7, 30), DAY, priority="High")
    second = Task("Second", time(7, 30), DAY, priority="High")
    buddy.add_task(first)
    buddy.add_task(second)

    assert scheduler.sort_by_time([first, second]) == [first, second]


def test_find_next_available_slot_skips_chained_task_intervals():
    owner = Owner("Jordan")
    buddy = Pet("Buddy", "dog")
    owner.add_pet(buddy)
    buddy.add_task(
        Task("Walk", time(7, 0), DAY, duration_minutes=60)
    )
    buddy.add_task(
        Task("Breakfast", time(8, 0), DAY, duration_minutes=60)
    )
    scheduler = Scheduler(owner)

    slot = scheduler.find_next_available_slot(
        datetime.combine(DAY, time(7, 30)), timedelta(minutes=30)
    )

    assert slot == datetime.combine(DAY, time(9, 0))


def test_find_next_available_slot_ignores_completed_tasks_and_allows_boundary():
    owner = Owner("Jordan")
    buddy = Pet("Buddy", "dog")
    owner.add_pet(buddy)
    completed = Task("Walk", time(7, 0), DAY, duration_minutes=60, completed=True)
    buddy.add_task(completed)
    buddy.add_task(Task("Breakfast", time(8, 0), DAY, duration_minutes=30))
    scheduler = Scheduler(owner)

    slot = scheduler.find_next_available_slot(
        datetime.combine(DAY, time(8, 30)), timedelta(minutes=30)
    )

    assert slot == datetime.combine(DAY, time(8, 30))


def test_find_next_available_slot_considers_tasks_after_midnight():
    owner = Owner("Jordan")
    buddy = Pet("Buddy", "dog")
    owner.add_pet(buddy)
    buddy.add_task(Task("Late walk", time(23, 30), DAY, duration_minutes=60))
    tomorrow = DAY + timedelta(days=1)
    buddy.add_task(Task("Breakfast", time(0, 30), tomorrow, duration_minutes=30))
    scheduler = Scheduler(owner)

    slot = scheduler.find_next_available_slot(
        datetime.combine(DAY, time(23, 45)), timedelta(minutes=30)
    )

    assert slot == datetime.combine(tomorrow, time(1, 0))


@pytest.mark.parametrize(
    "start,duration",
    [
        (datetime(2026, 10, 18, 8), timedelta(0)),
        (datetime(2026, 10, 18, 8), timedelta(minutes=-1)),
        (datetime(2026, 10, 18, 8).astimezone(), timedelta(minutes=30)),
    ],
)
def test_find_next_available_slot_rejects_invalid_inputs(start, duration):
    _, scheduler = make_scheduler()
    with pytest.raises(ValueError):
        scheduler.find_next_available_slot(start, duration)


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


def test_streamlit_add_task_and_complete_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()
    assert not app.exception
    assert any(message.value.startswith("No pets added yet.") for message in app.info)

    app.text_input[1].set_value("Buddy")
    app.button(key="FormSubmitter:add_pet_form-Add pet").click().run()
    assert not app.exception
    assert any(message.value == "Added Buddy the dog." for message in app.success)

    app.text_input[2].set_value("Breakfast")
    next(item for item in app.selectbox if item.label == "Repeat").select("daily")
    next(item for item in app.selectbox if item.label == "Priority").select("High")
    app.button(key="FormSubmitter:add_task_form-Add task").click().run()
    assert not app.exception
    assert any(message.value == "Added 'Breakfast' for Buddy." for message in app.success)
    assert any(button.label == "Complete" for button in app.button)

    due_date = app.date_input[0].value
    next(button for button in app.button if button.label == "Complete").click().run()
    assert not app.exception
    assert any(message.value == "Done" for message in app.success)
    next_date = due_date + timedelta(days=1)
    assert any(next_date.strftime("%b %d") in item.value for item in app.caption)
    restored_owner = Owner.load_from_json()
    restored_tasks = restored_owner.get_pet("Buddy").tasks
    assert restored_tasks[0].completed is True
    assert restored_tasks[1].due_date == next_date
    assert restored_tasks[1].completed is False
    assert restored_tasks[0].priority == "High"
    assert restored_tasks[1].priority == "High"
    restarted_app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()
    assert not restarted_app.exception
    assert any("Breakfast" in item.value for item in restarted_app.markdown)
    assert any(message.value == "Done" for message in restarted_app.success)


def test_streamlit_validation_and_duplicate_pet_feedback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()

    app.button(key="FormSubmitter:add_pet_form-Add pet").click().run()
    assert any("Please enter a pet name." == message.value for message in app.warning)

    app.text_input[1].set_value("Buddy")
    app.button(key="FormSubmitter:add_pet_form-Add pet").click().run()
    app.text_input[1].set_value("Buddy")
    app.button(key="FormSubmitter:add_pet_form-Add pet").click().run()
    assert any("already exists" in message.value for message in app.error)

    app.text_input[2].set_value(" ")
    app.button(key="FormSubmitter:add_task_form-Add task").click().run()
    assert any("Please enter a task description." == message.value for message in app.warning)


def test_streamlit_conflict_warning_is_visible_through_filters():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py")
    owner = Owner("Jordan")
    buddy = Pet("Buddy", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(buddy)
    owner.add_pet(luna)
    buddy.add_task(Task("Breakfast", time(8, 0), DAY))
    luna.add_task(Task("Medication", time(8, 0), DAY))
    app.session_state["owner"] = owner
    app.run()

    next(item for item in app.selectbox if item.label == "Filter by pet").select("Buddy")
    app.run()

    assert not app.exception
    assert any(
        "Conflict on Oct 18 at 08:00 AM — Buddy: Breakfast, Luna: Medication"
        in warning.value
        for warning in app.warning
    )
    assert any(
        "even when schedule filters hide a task" in caption.value for caption in app.caption
    )
    assert any("Breakfast" in item.value for item in app.markdown)
    assert not any("Medication" in item.value for item in app.markdown)


def test_streamlit_finds_next_available_slot_using_task_duration(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py")
    owner = Owner("Jordan")
    buddy = Pet("Buddy", "dog")
    owner.add_pet(buddy)
    buddy.add_task(Task("Walk", time(8, 0), DAY, duration_minutes=45))
    app.session_state["owner"] = owner

    app.run()
    next(widget for widget in app.date_input if widget.label == "Start searching on").set_value(
        DAY
    )
    next(widget for widget in app.time_input if widget.label == "Start searching at").set_value(
        time(8, 0)
    )
    app.button(key="FormSubmitter:find_slot_form-Find next available slot").click().run()

    assert not app.exception
    assert any(
        "Next available slot: Sunday, Oct 18 at 08:45 AM – 09:15 AM." in message.value
        for message in app.success
    )
