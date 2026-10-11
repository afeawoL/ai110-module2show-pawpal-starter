import streamlit as st

from pawpal_system import WINDOWS, Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITY_BADGE = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}


def when_label(task: Task) -> str:
    """Show a task's exact time, else its preferred window, else 'Any time'."""
    if task.fixed_time:
        return f"{task.fixed_time:%H:%M}"
    return (task.preferred_window or "any time").capitalize()

st.title("🐾 PawPal+")
st.markdown("Plan your pets' care for the day based on your time, priorities, and preferences.")

# Streamlit reruns this script on every interaction, so keep the Owner in
# session_state: it's created once and reused on every rerun after that.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)
owner = st.session_state.owner

st.divider()

# --- Owner ---
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

col1, col2, col3 = st.columns(3)
with col1:
    available = st.number_input(
        "Available minutes", min_value=0, max_value=1440, value=owner.available_minutes, step=15
    )
with col2:
    day_start = st.time_input("Day starts", value=owner.day_start, step=900)
with col3:
    day_end = st.time_input("Day ends", value=owner.day_end, step=900)

try:
    owner.set_constraints(int(available), day_start, day_end)
except ValueError as e:
    st.error(str(e))

st.divider()

# --- Pets ---
st.subheader("Pets")

with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age", min_value=0, max_value=40, value=3)
    special_needs = st.text_input("Special needs (optional)")

    if st.form_submit_button("Add pet"):
        try:
            owner.add_pet(Pet(
                name=pet_name.strip(),
                species=species,
                age=int(age),
                special_needs=special_needs.strip() or None,
            ))
            st.success(f"Added {pet_name}.")
        except ValueError as e:
            st.error(str(e))

if owner.pets:
    st.table([
        {"Name": p.name, "Species": p.species, "Age": p.age,
         "Special needs": p.special_needs or "", "Tasks": len(p.tasks)}
        for p in owner.pets
    ])
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Tasks ---
st.subheader("Tasks")
time_conflicts: list[str] = []

if not owner.pets:
    st.caption("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        target_pet = st.selectbox("For pet", [p.name for p in owner.pets])

        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

        col4, col5, col6, col7 = st.columns(4)
        with col4:
            category = st.selectbox("Category", ["", "feeding", "exercise", "meds", "grooming"])
        with col5:
            window = st.selectbox("Preferred time", ["any"] + list(WINDOWS))
        with col6:
            fixed_time = st.time_input("Exact time (optional)", value=None, step=900)
        with col7:
            recurrence = st.selectbox("Repeats", ["none", "daily", "weekly"])

        if st.form_submit_button("Add task"):
            try:
                owner.get_pet(target_pet).add_task(Task(
                    title=task_title.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    category=category or None,
                    preferred_window=None if window == "any" else window,
                    fixed_time=fixed_time,
                    recurrence=None if recurrence == "none" else recurrence,
                ))
                st.success(f"Added '{task_title}' for {target_pet}.")
            except ValueError as e:
                st.error(str(e))

    # Lightweight conflict check: warn right away about overlapping fixed-time tasks.
    scheduler = Scheduler(owner)
    time_conflicts = scheduler.check_conflicts()
    for warning in time_conflicts:
        st.warning(warning, icon="⚠️")

    # Mark a task complete; recurring tasks get their next occurrence automatically.
    todo = {task.id: (pet, task) for pet, task in owner.filter_tasks(completed=False)}
    if todo:
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        with col1:
            done_id = st.selectbox(
                "Mark a task complete",
                list(todo),
                format_func=lambda tid: f"{todo[tid][1].title} ({todo[tid][0].name}, due {todo[tid][1].due_date:%b %d})",
            )
        with col2:
            if st.button("Mark complete"):
                task = todo[done_id][1]
                next_task = scheduler.mark_task_complete(done_id)
                if next_task:
                    st.success(f"Done! Next '{task.title}' is due {next_task.due_date:%A, %b %d}.", icon="🔁")
                else:
                    st.success(f"Done: '{task.title}'.", icon="✅")

    # Filter with Owner.filter_tasks, then sort with the Scheduler.
    st.markdown("##### Task list")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        pet_filter = st.selectbox("Pet", ["All pets"] + [p.name for p in owner.pets])
    with col2:
        status_filter = st.selectbox("Status", ["All", "To do", "Done"])
    with col3:
        priority_filter = st.selectbox("Priority", ["All", "high", "medium", "low"], key="priority_filter")
    with col4:
        sort_by = st.selectbox("Sort by", ["Time of day", "Priority", "Date added"])

    shown = owner.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "To do": False, "Done": True}[status_filter],
        priority=None if priority_filter == "All" else priority_filter,
    )
    pet_of = {task.id: pet for pet, task in shown}
    tasks = [task for _, task in shown]
    if sort_by == "Time of day":
        tasks = scheduler.sort_by_time(tasks)
    elif sort_by == "Priority":
        tasks = scheduler.rank_tasks(tasks)

    if tasks:
        st.dataframe(
            [
                {"When": when_label(t), "Task": t.title, "Pet": pet_of[t.id].name,
                 "Priority": PRIORITY_BADGE[t.priority.value], "Minutes": t.duration_minutes,
                 "Category": (t.category or "").capitalize(), "Repeats": (t.recurrence or "").capitalize(),
                 "Due": t.due_date, "Done": t.completed}
                for t in tasks
            ],
            hide_index=True,
            use_container_width=True,
            column_config={
                "Minutes": st.column_config.NumberColumn(format="%d min"),
                "Due": st.column_config.DateColumn(format="MMM D"),
                "Done": st.column_config.CheckboxColumn(),
            },
        )
        st.caption(f"Showing {len(tasks)} of {len(owner.get_all_tasks())} tasks · sorted by {sort_by.lower()}")
    elif owner.get_all_tasks():
        st.info("No tasks match these filters.", icon="🔍")
    else:
        st.info("No tasks yet. Add one above.", icon="📝")

st.divider()

# --- Schedule ---
st.subheader("Build Schedule")

if st.button("Generate schedule", type="primary"):
    if not owner.get_all_tasks():
        st.warning("Add at least one task before generating a schedule.", icon="📝")
    elif not owner.filter_tasks(completed=False):
        st.success("Everything is done. Nothing left to schedule today!", icon="🎉")
    else:
        plan = Scheduler(owner).generate_plan()
        budget = owner.daily_budget()
        used = plan.total_time_used()

        st.markdown(f"### Today's Schedule · {plan.date:%A, %B %d}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Scheduled", len(plan.scheduled_items))
        col2.metric("Skipped", len(plan.unscheduled_items))
        col3.metric("Time used", f"{used} min")
        col4.metric("Free", f"{plan.time_remaining(budget)} min")
        st.progress(min(used / budget, 1.0) if budget else 0.0, text=f"{used} of {budget} budget minutes used")

        # Overall verdict
        if not plan.unscheduled_items and not plan.warnings:
            st.success(f"All {len(plan.scheduled_items)} tasks fit with no conflicts.", icon="✅")
        elif plan.unscheduled_items:
            st.warning(f"{len(plan.unscheduled_items)} task(s) didn't fit today. See below.", icon="⏳")

        if plan.scheduled_items:
            st.dataframe(
                [
                    {"Time": item.span(), "Task": item.task.title, "Pet": item.pet.name,
                     "Priority": PRIORITY_BADGE[item.task.priority.value],
                     "Minutes": item.duration(), "Why": item.reason}
                    for item in plan.scheduled_items
                ],
                hide_index=True,
                use_container_width=True,
                column_config={"Minutes": st.column_config.NumberColumn(format="%d min")},
            )
        else:
            st.info("Nothing could be scheduled in the time available.", icon="🕒")

        if plan.unscheduled_items:
            st.markdown("##### Skipped today")
            st.dataframe(
                [
                    {"Task": task.title, "Priority": PRIORITY_BADGE[task.priority.value],
                     "Minutes": task.duration_minutes, "Reason": reason}
                    for task, reason in plan.unscheduled_items
                ],
                hide_index=True,
                use_container_width=True,
                column_config={"Minutes": st.column_config.NumberColumn(format="%d min")},
            )

        # Time clashes are already shown under Tasks; point to them only if they made it
        # into the plan, and show the plan's other warnings (windows, duplicates) here.
        shown_above = [w for w in plan.warnings if w in time_conflicts]
        if shown_above:
            st.warning(f"{len(shown_above)} time conflict(s) in this plan. See the Tasks section.", icon="⚠️")
        for warning in (w for w in plan.warnings if w not in time_conflicts):
            st.warning(warning, icon="⚠️")
