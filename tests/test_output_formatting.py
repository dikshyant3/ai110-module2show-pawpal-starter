from datetime import date, time

from output_formatting import format_task_table, task_emoji, task_status
from pawpal_system import Task


def test_task_emoji_matches_common_care_types_and_falls_back():
    assert task_emoji("Evening walk") == "🚶"
    assert task_emoji("Give flea medication") == "💊"
    assert task_emoji("Unusual care activity") == "🐾"


def test_task_status_has_distinct_completed_and_pending_indicators():
    assert task_status(True) == "✅ Done"
    assert task_status(False) == "⏳ Pending"


def test_task_table_includes_readable_fields_and_optional_terminal_color():
    task = Task("Morning walk", time(7, 30), date(2026, 10, 19), pet_name="Buddy")

    table = format_task_table([task])
    assert "Type" in table
    assert "🚶" in table
    assert "Buddy" in table
    assert "Morning walk" in table
    assert "⏳ Pending" in table
    assert "\033[" not in table

    colored_table = format_task_table([task], color=True)
    assert "\033[33m⏳ Pending\033[0m" in colored_table


def test_task_table_empty_state():
    assert format_task_table([]) == "No tasks scheduled."
