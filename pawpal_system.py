"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from datetime import date, time, timedelta
from typing import Optional


RECURRENCE_INTERVALS = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


@dataclass
class Task:
    """A single pet care activity (feeding, walk, medication, etc.)."""

    description: str
    scheduled_time: time
    due_date: date
    frequency: str = "once"  # "once", "daily", or "weekly"
    completed: bool = False
    pet_name: str = ""  # set by Pet.add_task so the Scheduler knows whose task it is

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self) -> Optional[Task]:
        """Return a new Task for the next daily/weekly occurrence, or None if one-time."""
        if self.frequency not in RECURRENCE_INTERVALS:
            return None
        return Task(
            self.description,
            self.scheduled_time,
            self.due_date + RECURRENCE_INTERVALS[self.frequency],
            self.frequency,
            pet_name=self.pet_name,
        )


@dataclass
class Pet:
    """A pet and the care tasks assigned to it."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Tag any tasks passed to the constructor with this pet's name."""
        for task in self.tasks:
            task.pet_name = self.name

    def add_task(self, task: Task) -> None:
        """Assign a task to this pet and set task.pet_name to this pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_task(
        self,
        description: str,
        due_date: Optional[date] = None,
        scheduled_time: Optional[time] = None,
    ) -> Optional[Task]:
        """Return the single incomplete task matching description (and date/time if given).

        Returns None if nothing matches. Raises ValueError if several tasks match, so the
        caller must pass due_date and/or scheduled_time to say which one it means.
        """
        matches = [
            task
            for task in self.tasks
            if task.description == description
            and not task.completed
            and (due_date is None or task.due_date == due_date)
            and (scheduled_time is None or task.scheduled_time == scheduled_time)
        ]
        if len(matches) > 1:
            raise ValueError(
                f"{len(matches)} incomplete tasks named {description!r} for {self.name}; "
                "pass due_date and/or scheduled_time to choose one."
            )
        return matches[0] if matches else None


@dataclass
class Owner:
    """A pet owner who manages one or more pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner; raise ValueError if a pet with that name already exists."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"A pet named {pet.name!r} already exists.")
        self.pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Return the pet with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


class Scheduler:
    """Organizes tasks across all pets, accessed through the Owner."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def get_schedule(self, day: Optional[date] = None) -> list[Task]:
        """Return all tasks across every pet, or only those due on the given day."""
        tasks = self.owner.get_all_tasks()
        if day is None:
            return tasks
        return [task for task in tasks if task.due_date == day]

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return the tasks ordered by due date, then scheduled time."""
        return sorted(tasks, key=lambda task: (task.due_date, task.scheduled_time))

    def filter_tasks(
        self, pet_name: Optional[str] = None, completed: Optional[bool] = None
    ) -> list[Task]:
        """Return tasks matching the given pet name and/or completion status."""
        return [
            task
            for task in self.owner.get_all_tasks()
            if (pet_name is None or task.pet_name == pet_name)
            and (completed is None or task.completed == completed)
        ]

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return warning messages for tasks scheduled at the same date and time.

        Only incomplete tasks count; a task that is already done can't clash with anything.
        """
        slots: dict[tuple[date, time], list[Task]] = defaultdict(list)
        for task in tasks:
            if not task.completed:
                slots[(task.due_date, task.scheduled_time)].append(task)

        warnings = []
        for (due_date, scheduled_time), clashing in sorted(slots.items()):
            if len(clashing) > 1:
                names = ", ".join(f"{task.pet_name}: {task.description}" for task in clashing)
                warnings.append(
                    f"Conflict on {due_date:%b %d} at {scheduled_time:%I:%M %p} — {names}"
                )
        return warnings

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark this exact task complete; if recurring, add and return its next occurrence."""
        if task.completed:
            raise ValueError(f"Task {task.description!r} is already completed.")
        pet = self.owner.get_pet(task.pet_name)
        if pet is None or not any(t is task for t in pet.tasks):
            raise ValueError(f"Task {task.description!r} does not belong to this owner's pets.")

        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def mark_task_complete(
        self,
        pet_name: str,
        description: str,
        due_date: Optional[date] = None,
        scheduled_time: Optional[time] = None,
    ) -> Optional[Task]:
        """Mark a pet's task complete; if recurring, add its next occurrence to that pet.

        Looks up the pet via owner.get_pet(pet_name), then the task via pet.get_task(...).
        If the description alone matches several incomplete tasks, raises ValueError;
        pass due_date and/or scheduled_time to pick one.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"Pet {pet_name!r} not found.")

        task = pet.get_task(description, due_date, scheduled_time)
        if task is None:
            raise ValueError(
                f"No incomplete task named {description!r} found for {pet_name}."
            )

        return self.complete_task(task)
