"""Demo script for the PawPal+ backend."""

from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    """Build a sample owner with two pets and print today's schedule."""
    today = date.today()

    owner = Owner("Jordan")
    buddy = Pet("Buddy", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(buddy)
    owner.add_pet(luna)

    buddy.add_task(Task("Morning walk", time(7, 30), today, "daily"))
    buddy.add_task(Task("Breakfast", time(8, 0), today, "daily"))
    luna.add_task(Task("Flea medication", time(12, 0), today, "weekly"))
    luna.add_task(Task("Play session", time(18, 15), today))

    buddy.tasks[0].mark_complete()

    scheduler = Scheduler(owner)

    print(f"Today's Schedule for {owner.name} ({today:%A, %B %d, %Y})")
    print("-" * 50)
    for task in scheduler.get_schedule(today):
        status = "Done" if task.completed else "Pending"
        print(f"{task.scheduled_time:%I:%M %p}  {task.pet_name:<6}  {task.description:<16}  [{status}]")


if __name__ == "__main__":
    main()
