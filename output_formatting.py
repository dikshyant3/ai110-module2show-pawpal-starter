"""Presentation helpers shared by the PawPal+ app and CLI demo."""

from __future__ import annotations

from collections.abc import Sequence

from pawpal_system import Task


_TASK_EMOJI_KEYWORDS = (
    (("medication", "medicine", "pill", "flea", "dose"), "💊"),
    (("vet", "appointment", "checkup", "check-up"), "🩺"),
    (("feed", "food", "breakfast", "lunch", "dinner", "meal"), "🍽️"),
    (("walk", "exercise", "run"), "🚶"),
    (("play", "enrichment", "toy"), "🎾"),
    (("groom", "bath", "brush"), "🛁"),
    (("litter", "clean", "tidy"), "🧹"),
)
_WIDE_EMOJI = frozenset("🚶💊🩺🍽️🎾🛁🧹🐾✅⏳")


def task_emoji(description: str) -> str:
    """Return an emoji for a common care-task type, or paws as a fallback."""
    normalized = description.casefold()
    for keywords, emoji in _TASK_EMOJI_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return emoji
    return "🐾"


def task_status(completed: bool) -> str:
    """Return a compact, color-emoji status label for a task."""
    return "✅ Done" if completed else "⏳ Pending"


def format_task_table(tasks: Sequence[Task], *, color: bool = False) -> str:
    """Format tasks as an aligned text table; optionally color status labels for terminals."""
    if not tasks:
        return "No tasks scheduled."

    headers = ("Type", "Date", "Time", "Priority", "Pet", "Task", "Repeat", "Status")
    rows = [
        (
            task_emoji(task.description),
            task.due_date.strftime("%b %d"),
            task.scheduled_time.strftime("%I:%M %p"),
            task.priority,
            task.pet_name,
            " ".join(task.description.split()),
            task.frequency,
            task_status(task.completed),
        )
        for task in tasks
    ]

    def display_width(value: str, column: int) -> int:
        has_leading_emoji = (
            column in (0, len(headers) - 1) and bool(value) and value[0] in _WIDE_EMOJI
        )
        return len(value) + int(has_leading_emoji)

    widths = [
        max(
            display_width(headers[index], index),
            *(display_width(row[index], index) for row in rows),
        )
        for index in range(len(headers))
    ]
    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    def render_row(values: Sequence[str], *, status: bool = False) -> str:
        cells = []
        for index, (value, width) in enumerate(zip(values, widths)):
            padding = " " * (width - display_width(value, index))
            padded = value + padding
            if color and status and index == len(headers) - 1:
                ansi_color = "\033[32m" if value.startswith("✅") else "\033[33m"
                padded = f"{ansi_color}{value}\033[0m" + padding
            cells.append(padded)
        return "| " + " | ".join(cells) + " |"

    return "\n".join(
        (separator, render_row(headers), separator)
        + tuple(render_row(row, status=True) for row in rows)
        + (separator,)
    )
