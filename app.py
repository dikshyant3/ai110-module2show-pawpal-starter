from datetime import date, datetime, time, timedelta
from pathlib import Path

import streamlit as st

from output_formatting import task_emoji, task_status
from pawpal_system import Owner, Pet, Scheduler, Task

DATA_FILE = Path("data.json")


def complete_task_and_save(task: Task) -> None:
    """Complete a task and persist the updated household."""
    owner = st.session_state.owner
    Scheduler(owner).complete_task(task)
    owner.save_to_json(DATA_FILE)


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan and track the care routines that keep your pets happy and healthy.")

st.divider()

st.subheader("Your household")
owner_name = st.text_input(
    "Owner name",
    value="Jordan",
    help="Used when your PawPal+ session starts.",
)

# Create the Owner only once; Streamlit reruns this script on every interaction.
if "owner" not in st.session_state:
    st.session_state.owner = (
        Owner.load_from_json(DATA_FILE) if DATA_FILE.exists() else Owner(owner_name)
    )
owner = st.session_state.owner

with st.expander("Save or load household data"):
    st.download_button(
        "Download household JSON",
        data=owner.to_json(),
        file_name="data.json",
        mime="application/json",
    )
    st.caption("Changes are also saved automatically in data.json for the next run.")

    with st.form("load_household_form"):
        uploaded_json = st.file_uploader("Choose a PawPal+ JSON file", type=["json"])
        load_clicked = st.form_submit_button("Load household")

    if load_clicked:
        if uploaded_json is None:
            st.warning("Choose a JSON file before loading.")
        else:
            try:
                owner = Owner.from_json(uploaded_json.getvalue())
                owner.save_to_json(DATA_FILE)
                st.session_state.owner = owner
                st.success(f"Loaded household for {owner.name}.")
            except ValueError as error:
                st.error(f"Could not load household: {error}")

st.divider()

st.subheader("Pets")
st.caption("Add each pet once, then assign care tasks to them.")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name", help="Use a distinct name for each pet.")
    species = st.selectbox("Pet species", ["dog", "cat", "other"])
    add_pet_clicked = st.form_submit_button("Add pet")

if add_pet_clicked:
    if not pet_name.strip():
        st.warning("Please enter a pet name.")
    else:
        try:
            owner.add_pet(Pet(pet_name.strip(), species))
            owner.save_to_json(DATA_FILE)
            st.success(f"Added {pet_name.strip()} the {species}.")
        except ValueError as error:
            st.error(str(error))

if owner.pets:
    st.caption(f"{len(owner.pets)} pet{'s' if len(owner.pets) != 1 else ''} in your household")
    st.dataframe(
        [{"Pet": pet.name, "Species": pet.species.title()} for pet in owner.pets],
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info("No pets added yet. Add your first pet above to get started.")

st.divider()

st.subheader("Care tasks")
st.caption("Schedule a one-time activity or set a daily or weekly routine.")
if not owner.pets:
    st.info("Add a pet before creating care tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        task_pet_name = st.selectbox("Assign to pet", [pet.name for pet in owner.pets])
        description = st.text_input(
            "What needs to be done?",
            help="For example: breakfast, evening walk, or medication.",
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            scheduled_time = st.time_input("Scheduled time")
        with col2:
            due_date = st.date_input("Due date")
        with col3:
            frequency = st.selectbox(
                "Repeat",
                ["once", "daily", "weekly"],
                help="Recurring tasks create the next occurrence when completed.",
            )
        priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=1)
        duration_minutes = st.number_input(
            "Duration (minutes)", min_value=1, max_value=1440, value=30, step=5
        )
        add_task_clicked = st.form_submit_button("Add task")

    if add_task_clicked:
        if not description.strip():
            st.warning("Please enter a task description.")
        else:
            pet = owner.get_pet(task_pet_name)
            pet.add_task(
                Task(
                    description.strip(),
                    scheduled_time,
                    due_date,
                    frequency,
                    duration_minutes=int(duration_minutes),
                    priority=priority,
                )
            )
            owner.save_to_json(DATA_FILE)
            st.success(f"Added '{description.strip()}' for {pet.name}.")

st.divider()

st.subheader("Care schedule")
st.caption(
    "Tasks are ordered by priority, then date and time. Completing a recurring task adds its next occurrence."
)

scheduler = Scheduler(owner)

with st.form("find_slot_form"):
    st.caption("Find the earliest opening for a task of the requested duration.")
    slot_col1, slot_col2, slot_col3 = st.columns(3)
    with slot_col1:
        slot_start_date = st.date_input("Start searching on", value=date.today())
    with slot_col2:
        slot_start_time = st.time_input("Start searching at", value=time(8, 0))
    with slot_col3:
        slot_duration_minutes = st.number_input(
            "Requested duration (minutes)",
            min_value=1,
            max_value=1440,
            value=30,
            step=5,
        )
    find_slot_clicked = st.form_submit_button("Find next available slot")

if find_slot_clicked:
    slot_start = datetime.combine(slot_start_date, slot_start_time)
    available_start = scheduler.find_next_available_slot(
        slot_start, timedelta(minutes=int(slot_duration_minutes))
    )
    available_end = available_start + timedelta(minutes=int(slot_duration_minutes))
    end_label = (
        f"{available_end:%A, %b %d at %I:%M %p}"
        if available_end.date() != available_start.date()
        else f"{available_end:%I:%M %p}"
    )
    st.success(
        f"Next available slot: {available_start:%A, %b %d at %I:%M %p} – {end_label}."
    )

# Conflicts are checked across every task, so a filter can't hide a clash.
all_conflicts = scheduler.detect_conflicts(scheduler.get_schedule())
if all_conflicts:
    st.subheader("Scheduling conflicts")
    st.caption(
        "These warnings include all pets and dates, even when schedule filters hide a task. "
        "Check the date, time, pet, and task names, then reschedule one of the clashing tasks."
    )
    for warning in all_conflicts:
        st.warning(warning)
elif owner.get_all_tasks():
    st.success("No pending tasks share the exact same date and time.")

# Widget keys keep the filter choices in session_state across reruns.
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    pet_filter = st.selectbox(
        "Filter by pet",
        ["All pets"] + [pet.name for pet in owner.pets],
        key="filter_pet",
    )
with filter_col2:
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "Pending", "Done"],
        key="filter_status",
    )

schedule = scheduler.sort_by_time(
    scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "Pending": False, "Done": True}[status_filter],
    )
)

if not schedule:
    if not owner.get_all_tasks():
        st.info("No care tasks yet. Add a task above to build your schedule.")
    else:
        st.info("No tasks match these filters. Try a different pet or status.")
else:
    table_columns = st.columns([3, 1.2, 2, 1.2, 1.8])
    for column, heading in zip(
        table_columns, ("Task", "Pet", "Scheduled", "Priority", "Status / action")
    ):
        column.markdown(f"**{heading}**")

    for task in schedule:
        task_col, pet_col, schedule_col, priority_col, status_col = st.columns(
            [3, 1.2, 2, 1.2, 1.8]
        )
        task_col.markdown(f"**{task_emoji(task.description)} {task.description}**")
        task_col.caption(f"{task.frequency.title()} · {task.duration_minutes} min")
        pet_col.write(task.pet_name)
        schedule_col.caption(
            f"{task.due_date:%b %d} · {task.scheduled_time:%I:%M %p}"
        )
        priority_color = {"High": "red", "Medium": "orange", "Low": "blue"}[
            task.priority
        ]
        priority_col.markdown(f":{priority_color}[{task.priority}]")
        if task.completed:
            status_col.success(task_status(task.completed))
        else:
            status_col.warning(task_status(task.completed))
            # Pass the task object itself so equal descriptions cannot complete the
            # wrong task. The object remains in session state across reruns.
            status_col.button(
                "Complete",
                key=f"complete_{id(task)}",
                on_click=complete_task_and_save,
                args=(task,),
                help="Mark this task complete.",
            )
