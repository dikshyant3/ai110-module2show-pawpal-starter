"""Demo script for the PawPal+ backend."""

import sys
from datetime import date, time

from output_formatting import format_task_table
from pawpal_system import Owner, Pet, Scheduler, Task


def print_tasks(title: str, tasks: list[Task]) -> None:
    """Print a heading followed by a formatted task table."""
    print(f"\n{title}")
    print(format_task_table(tasks, color=sys.stdout.isatty()))


def main() -> None:
    """Build a sample owner with two pets and demo sorting, filtering, conflicts, and recurrence."""
    today = date.today()

    owner = Owner("Jordan")
    buddy = Pet("Buddy", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(buddy)
    owner.add_pet(luna)

    # Added out of order on purpose so priority sorting has something to do.
    luna.add_task(Task("Play session", time(6, 15), today, priority="Low"))
    buddy.add_task(Task("Breakfast", time(8, 0), today, "daily"))
    luna.add_task(Task("Flea medication", time(11, 0), today, "weekly", priority="High"))
    buddy.add_task(Task("Morning walk", time(7, 30), today, "daily", priority="High"))
    # Same date and time as Buddy's breakfast, to trigger a conflict warning.
    luna.add_task(Task("Breakfast", time(8, 0), today, "daily"))

    scheduler = Scheduler(owner)

    print(f"PawPal+ demo for {owner.name} ({today:%A, %B %d, %Y})")

    print_tasks("Unsorted (grouped by pet, in the order added)", scheduler.get_schedule(today))
    print_tasks(
        "Sorted by priority, date, and time",
        scheduler.sort_by_time(scheduler.get_schedule(today)),
    )

    print("\nConflicts")
    print("-" * 60)
    for warning in scheduler.detect_conflicts(scheduler.get_schedule(today)) or ["None"]:
        print(warning)

    # Completing a daily task adds tomorrow's copy automatically.
    next_walk = scheduler.mark_task_complete("Buddy", "Morning walk")
    print(f"\nCompleted Buddy's Morning walk -> next one added for {next_walk.due_date:%b %d}")

    print_tasks("Filter: Buddy only", scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Buddy")))
    print_tasks("Filter: completed", scheduler.filter_tasks(completed=True))
    print_tasks(
        "Filter: Luna, pending", scheduler.sort_by_time(scheduler.filter_tasks("Luna", False))
    )


if __name__ == "__main__":
    main()
