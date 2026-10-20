"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4


RECURRENCE_INTERVALS = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
PRIORITY_RANKS = {"High": 0, "Medium": 1, "Low": 2}


@dataclass
class Task:
    """A single pet care activity (feeding, walk, medication, etc.)."""

    description: str
    scheduled_time: time
    due_date: date
    frequency: str = "once"  # "once", "daily", or "weekly"
    completed: bool = False
    pet_name: str = ""  # set by Pet.add_task so the Scheduler knows whose task it is
    task_id: str = field(default_factory=lambda: str(uuid4()), compare=False)
    duration_minutes: int = 30
    priority: str = "Medium"

    def __post_init__(self) -> None:
        """Validate the task's duration and priority."""
        if (
            isinstance(self.duration_minutes, bool)
            or not isinstance(self.duration_minutes, int)
            or self.duration_minutes <= 0
        ):
            raise ValueError("Task duration must be a positive whole number of minutes.")
        if not isinstance(self.priority, str) or self.priority not in PRIORITY_RANKS:
            raise ValueError("Task priority must be Low, Medium, or High.")

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
            duration_minutes=self.duration_minutes,
            priority=self.priority,
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

    def to_dict(self) -> dict[str, object]:
        """Return this household as JSON-compatible data."""
        return {
            "version": 1,
            "owner": {
                "name": self.name,
                "pets": [
                    {
                        "name": pet.name,
                        "species": pet.species,
                        "tasks": [
                            {
                                "id": task.task_id,
                                "description": task.description,
                                "scheduled_time": task.scheduled_time.isoformat(),
                                "due_date": task.due_date.isoformat(),
                                "frequency": task.frequency,
                                "completed": task.completed,
                                "duration_minutes": task.duration_minutes,
                                "priority": task.priority,
                            }
                            for task in pet.tasks
                        ],
                    }
                    for pet in self.pets
                ],
            },
        }

    @classmethod
    def from_dict(cls, data: object) -> Owner:
        """Create a household from the versioned JSON-compatible representation."""
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("Unsupported or invalid PawPal+ JSON data.")

        owner_data = data.get("owner")
        if (
            not isinstance(owner_data, dict)
            or not isinstance(owner_data.get("name"), str)
            or not isinstance(owner_data.get("pets"), list)
        ):
            raise ValueError("PawPal+ JSON must contain an owner name and pets list.")

        owner = cls(owner_data["name"])
        task_ids: set[str] = set()
        for pet_data in owner_data["pets"]:
            if (
                not isinstance(pet_data, dict)
                or not isinstance(pet_data.get("name"), str)
                or not isinstance(pet_data.get("species"), str)
                or not isinstance(pet_data.get("tasks"), list)
            ):
                raise ValueError("Each pet must contain a name, species, and tasks list.")

            pet = Pet(pet_data["name"], pet_data["species"])
            for task_data in pet_data["tasks"]:
                if (
                    not isinstance(task_data, dict)
                    or not isinstance(task_data.get("id"), str)
                    or not isinstance(task_data.get("description"), str)
                    or not isinstance(task_data.get("scheduled_time"), str)
                    or not isinstance(task_data.get("due_date"), str)
                    or not isinstance(task_data.get("frequency"), str)
                    or not isinstance(task_data.get("completed"), bool)
                    or (
                        "priority" in task_data
                        and (
                            not isinstance(task_data["priority"], str)
                            or task_data["priority"] not in PRIORITY_RANKS
                        )
                    )
                    or (
                        "duration_minutes" in task_data
                        and (
                            isinstance(task_data["duration_minutes"], bool)
                            or not isinstance(task_data["duration_minutes"], int)
                            or task_data["duration_minutes"] <= 0
                        )
                    )
                ):
                    raise ValueError(
                        "Each task must contain its id, description, time, date, "
                        "frequency, and completion status, with an optional positive "
                        "whole-minute duration."
                    )
                if task_data["id"] in task_ids:
                    raise ValueError(f"Duplicate task ID {task_data['id']!r}.")
                task_ids.add(task_data["id"])

                pet.add_task(
                    Task(
                        task_data["description"],
                        time.fromisoformat(task_data["scheduled_time"]),
                        date.fromisoformat(task_data["due_date"]),
                        task_data["frequency"],
                        completed=task_data["completed"],
                        task_id=task_data["id"],
                        duration_minutes=task_data.get("duration_minutes", 30),
                        priority=task_data.get("priority", "Medium"),
                    )
                )
            owner.add_pet(pet)
        return owner

    def to_json(self) -> str:
        """Serialize this household to formatted JSON text."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_data: str | bytes) -> Owner:
        """Create a household from JSON text or bytes."""
        return cls.from_dict(json.loads(json_data))

    def save_to_json(self, path: str | Path = "data.json") -> None:
        """Write this household to a UTF-8 JSON file (data.json by default)."""
        Path(path).write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def load_from_json(cls, path: str | Path = "data.json") -> Owner:
        """Load a household from a UTF-8 JSON file (data.json by default)."""
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def save_json(self, path: str | Path = "data.json") -> None:
        """Backward-compatible alias for save_to_json()."""
        self.save_to_json(path)

    @classmethod
    def load_json(cls, path: str | Path = "data.json") -> Owner:
        """Backward-compatible alias for load_from_json()."""
        return cls.load_from_json(path)


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
        """Return tasks ordered by priority, then due date and scheduled time."""
        return sorted(
            tasks,
            key=lambda task: (
                PRIORITY_RANKS[task.priority],
                task.due_date,
                task.scheduled_time,
            ),
        )

    def find_next_available_slot(
        self, start: datetime, duration: timedelta
    ) -> datetime:
        """Return the earliest slot of ``duration`` not overlapping a pending task.

        Existing task intervals use each task's due date, scheduled time, and duration.
        The search considers tasks across every pet and can continue into later days.
        """
        if start.tzinfo is not None and start.utcoffset() is not None:
            raise ValueError("Start time must not include a timezone.")
        if duration <= timedelta(0):
            raise ValueError("Requested duration must be positive.")

        candidate = start
        pending_tasks = [task for task in self.owner.get_all_tasks() if not task.completed]
        busy_intervals: list[tuple[datetime, datetime]] = []
        for task in pending_tasks:
            busy_start = datetime.combine(task.due_date, task.scheduled_time)
            busy_end = busy_start + timedelta(minutes=task.duration_minutes)
            busy_intervals.append((busy_start, busy_end))
        while True:
            candidate_end = candidate + duration
            overlapping_ends = [
                busy_end
                for busy_start, busy_end in busy_intervals
                if candidate < busy_end and busy_start < candidate_end
            ]
            if not overlapping_ends:
                return candidate
            candidate = max(overlapping_ends)

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
