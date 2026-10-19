"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional


@dataclass
class Task:
    """A single pet care activity (feeding, walk, medication, etc.)."""

    description: str
    scheduled_time: time
    due_date: date
    frequency: str = "once"  # "once", "daily", or "weekly"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        pass

    def next_occurrence(self) -> Optional[Task]:
        """Return a new Task for the next daily/weekly occurrence, or None if one-time."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks assigned to it."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Assign a task to this pet."""
        pass

    def get_task(self, description: str) -> Optional[Task]:
        """Return the task with the given description, or None if not found."""
        pass


@dataclass
class Owner:
    """A pet owner who manages one or more pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def get_pet(self, name: str) -> Optional[Pet]:
        """Return the pet with the given name, or None if not found."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        pass


class Scheduler:
    """Organizes tasks across all pets, accessed through the Owner."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def get_schedule(self, day: date) -> list[Task]:
        """Return the tasks due on the given day, sorted by time."""
        pass

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return the tasks ordered by scheduled time."""
        pass

    def filter_tasks(
        self, pet_name: Optional[str] = None, completed: Optional[bool] = None
    ) -> list[Task]:
        """Return tasks matching the given pet name and/or completion status."""
        pass

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return warning messages for tasks scheduled at the same date and time."""
        pass

    def mark_task_complete(self, pet_name: str, description: str) -> None:
        """Mark a pet's task complete and schedule its next occurrence if recurring."""
        pass
