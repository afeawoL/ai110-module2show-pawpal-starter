"""Temporary testing ground: build a sample owner and print today's schedule."""

from datetime import date, time, timedelta

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def header(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def when(task: Task) -> str:
    if task.fixed_time:
        return f"at {task.fixed_time:%H:%M}"
    return task.preferred_window or "any time"


def print_tasks(pairs) -> None:
    for pet, task in pairs:
        done = "✓" if task.completed else " "
        print(f"  [{done}] {task.title:<14} {pet.name:<6} {when(task)}")


def main() -> None:
    today = date.today()
    owner = Owner(name="Jordan", available_minutes=150, day_start=time(7, 0), day_end=time(21, 0))

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5, special_needs="kidney diet")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of order: evening first, morning last.
    # Fixed times are "HH:MM" strings; "7:30" isn't zero-padded on purpose.
    mochi.add_task(Task("Evening walk", 30, Priority.MEDIUM, category="exercise",
                        preferred_window="evening", recurrence="daily"))
    luna.add_task(Task("Dinner", 5, Priority.HIGH, category="feeding",
                       fixed_time="18:00", recurrence="daily"))
    mochi.add_task(Task("Bath", 45, Priority.LOW, category="grooming"))
    luna.add_task(Task("Lunch meds", 5, Priority.HIGH, category="meds",
                       fixed_time="12:15", recurrence="daily"))
    luna.add_task(Task("Laser play", 20, Priority.MEDIUM, category="exercise",
                       preferred_window="evening"))
    mochi.add_task(Task("Breakfast", 10, Priority.HIGH, category="feeding",
                        fixed_time="7:30", recurrence="daily"))
    luna.add_task(Task("Kidney meds", 5, Priority.HIGH, category="meds",
                       fixed_time="7:30", recurrence="daily"))
    mochi.add_task(Task("Morning walk", 30, Priority.HIGH, category="exercise",
                        preferred_window="morning", recurrence="daily"))
    luna.add_task(Task("Brushing", 15, Priority.LOW, category="grooming", recurrence="weekly"))

    scheduler = Scheduler(owner)

    header("1. Tasks in the order they were added")
    print_tasks(owner.filter_tasks())

    header("2. Sorted by time with Scheduler.sort_by_time()")
    pet_of = {task.id: pet for pet, task in owner.filter_tasks()}
    for task in scheduler.sort_by_time(owner.get_all_tasks()):
        print(f"      {task.title:<14} {pet_of[task.id].name:<6} {when(task)}")

    header("3. Filter by pet: Luna only")
    print_tasks(owner.filter_tasks(pet_name="Luna"))

    header("3b. Conflict check (before scheduling)")
    # Add a clash on purpose: same pet, overlapping times. This warns, it doesn't crash.
    mochi.add_task(Task("Vet call", 15, Priority.HIGH, fixed_time="7:35"))
    for warning in scheduler.check_conflicts(today) or ["No conflicts."]:
        print(f"  ⚠ {warning}")

    header(f"4. Today's Schedule ({today:%A, %B %d})")
    plan = scheduler.generate_plan(today)
    print(plan.summary())

    header("5. Complete this morning's tasks")
    for item in plan.scheduled_items:
        if item.start_time < time(12, 0):
            next_task = scheduler.mark_task_complete(item.task.id, today)
            repeat = f"next due {next_task.due_date}" if next_task else "one-off, not repeated"
            print(f"  ✓ {item.task.title:<14} {repeat}")

    header("6. Filter by status: done")
    print_tasks(owner.filter_tasks(completed=True))

    header("7. Filter by status: still to do today")
    print_tasks(owner.filter_tasks(completed=False, due_on=today))

    header("8. Filter combined: Mochi's tasks still to do today")
    print_tasks(owner.filter_tasks(pet_name="Mochi", completed=False, due_on=today))

    header("9. Tomorrow's Schedule (daily tasks come back)")
    print(scheduler.generate_plan(today + timedelta(days=1)).summary())


if __name__ == "__main__":
    main()
