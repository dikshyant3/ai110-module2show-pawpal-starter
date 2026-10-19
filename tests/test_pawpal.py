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
