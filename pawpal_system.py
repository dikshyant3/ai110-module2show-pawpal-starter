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
    pet_name: str = ""  # set by Pet.add_task so the Scheduler knows whose task it is

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self) -> Optional[Task]:
        """Return a new Task for the next daily/weekly occurrence, or None if one-time."""
        pass


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

    def get_task(self, description: str) -> Optional[Task]:
        """Return the first incomplete task with the given description, or None if not found."""
        for task in self.tasks:
            if task.description == description and not task.completed:
                return task
        return None


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
        """Mark a pet's task complete; if recurring, add its next occurrence to that pet.

        Looks up the pet via owner.get_pet(pet_name), then the task via pet.get_task(description).
        """
        pet = self.owner.get_pet(pet_name)

        if pet is None:
         raise ValueError(f"Pet {pet_name!r} not found.")

        task = pet.get_task(description)

        if task is None:
            raise ValueError(
                f"No incomplete task named {description!r} found for {pet_name}."
            )

        task.mark_complete()
