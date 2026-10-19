import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

# Create the Owner only once; Streamlit reruns this script on every interaction.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(owner_name)
owner = st.session_state.owner

st.divider()

st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    add_pet_clicked = st.form_submit_button("Add pet")

if add_pet_clicked:
    if not pet_name.strip():
        st.warning("Please enter a pet name.")
    else:
        try:
            owner.add_pet(Pet(pet_name.strip(), species))
            st.success(f"Added {pet_name.strip()} the {species}.")
        except ValueError as error:
            st.error(str(error))

if owner.pets:
    st.write("Your pets:")
    st.table([{"Name": pet.name, "Species": pet.species} for pet in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Add a Task")
if not owner.pets:
    st.info("Add a pet first, then you can assign tasks to it.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        task_pet_name = st.selectbox("Pet", [pet.name for pet in owner.pets])
        description = st.text_input("Task description")
        col1, col2, col3 = st.columns(3)
        with col1:
            scheduled_time = st.time_input("Time")
        with col2:
            due_date = st.date_input("Due date")
        with col3:
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        add_task_clicked = st.form_submit_button("Add task")

    if add_task_clicked:
        if not description.strip():
            st.warning("Please enter a task description.")
        else:
            pet = owner.get_pet(task_pet_name)
            pet.add_task(Task(description.strip(), scheduled_time, due_date, frequency))
            st.success(f"Added '{description.strip()}' for {pet.name}.")

st.divider()

st.subheader("Schedule")
st.caption("Sorted by date and time. Completing a daily/weekly task adds its next occurrence.")

scheduler = Scheduler(owner)

# Conflicts are checked across every task, so a filter can't hide a clash.
for warning in scheduler.detect_conflicts(scheduler.get_schedule()):
    st.warning(warning)

# Widget keys keep the filter choices in session_state across reruns.
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    pet_filter = st.selectbox(
        "Pet", ["All pets"] + [pet.name for pet in owner.pets], key="filter_pet"
    )
with filter_col2:
    status_filter = st.selectbox("Status", ["All", "Pending", "Done"], key="filter_status")

schedule = scheduler.sort_by_time(
    scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "Pending": False, "Done": True}[status_filter],
    )
)

if not schedule:
    st.info("No tasks match. Add a task above or change the filters.")
else:
    for task in schedule:
        col_info, col_status = st.columns([4, 1])
        with col_info:
            st.write(
                f"**{task.scheduled_time:%I:%M %p}** · {task.due_date:%b %d} · "
                f"{task.pet_name} · {task.description} ({task.frequency})"
            )
        with col_status:
            if task.completed:
                st.write("✅ Done")
            else:
                # Pass the task object itself so tasks sharing a description can't be confused;
                # id() is stable because the tasks live in session_state. on_click runs before
                # the rerun, so the new status (and any next occurrence) shows immediately.
                st.button(
                    "Complete",
                    key=f"complete_{id(task)}",
                    on_click=scheduler.complete_task,
                    args=(task,),
                )
