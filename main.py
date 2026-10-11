"""Temporary testing ground: build a sample owner and print today's schedule."""

from datetime import time

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=120, day_start=time(7, 0), day_end=time(21, 0))

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5, special_needs="kidney diet")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("t1", "Morning walk", 30, Priority.HIGH, category="exercise", preferred_window="morning"))
    mochi.add_task(Task("t2", "Breakfast", 10, Priority.HIGH, category="feeding"))
    mochi.add_task(Task("t3", "Bath", 45, Priority.LOW, category="grooming"))
    luna.add_task(Task("t4", "Kidney meds", 5, Priority.HIGH, category="meds"))
    luna.add_task(Task("t5", "Laser play", 20, Priority.MEDIUM, category="exercise"))
    luna.add_task(Task("t6", "Brushing", 15, Priority.LOW, category="grooming"))

    plan = Scheduler(owner).generate_plan()

    print("=" * 60)
    print(f"Today's Schedule for {owner.name}'s pets ({plan.date:%A, %B %d})")
    print("=" * 60)

    for item in plan.scheduled_items:
        print(
            f"{item.start_time:%H:%M}-{item.end_time:%H:%M}  "
            f"{item.task.title:<14} {item.pet.name:<6} "
            f"{item.duration():>3} min  [{item.task.priority.value}]"
        )
        print(f"{'':13}why: {item.reason}")

    if plan.unscheduled_items:
        print("\nSkipped today:")
        for task, reason in plan.unscheduled_items:
            print(f"  - {task.title} ({task.duration_minutes} min): {reason}")

    if plan.warnings:
        print("\nWarnings:")
        for warning in plan.warnings:
            print(f"  ! {warning}")

    budget = owner.daily_budget()
    print("-" * 60)
    print(f"Time used: {plan.total_time_used()} / {budget} min "
          f"({plan.time_remaining(budget)} min free)")


if __name__ == "__main__":
    main()
