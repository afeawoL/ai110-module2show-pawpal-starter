from datetime import date, time, timedelta

import pytest

from pawpal_system import FreeTime, Owner, Pet, Priority, Scheduler, Task

DAY = date(2026, 10, 11)


def make_task(title, minutes=10, priority="high", **kwargs):
    kwargs.setdefault("due_date", DAY)
    return Task(title, minutes, priority, **kwargs)


def make_owner(minutes=240, start=time(8, 0), end=time(20, 0)):
    owner = Owner("Jordan", minutes, start, end)
    owner.add_pet(Pet("Mochi", "dog"))
    owner.add_pet(Pet("Luna", "cat"))
    return owner


def plan_for(owner):
    return Scheduler(owner).generate_plan(DAY)


# --- Basics ---

def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, Priority.HIGH)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", 10, Priority.HIGH))

    assert len(pet.tasks) == 1


def test_task_ids_are_generated_and_unique():
    a, b = Task("Walk", 10, "high"), Task("Walk", 10, "high")
    assert a.id and b.id and a.id != b.id


# --- Sorting by time ---

def test_sort_by_time_orders_fixed_then_window_then_untimed():
    meds = make_task("Meds", fixed_time=time(7, 30))
    play = make_task("Play", preferred_window="evening")
    walk = make_task("Walk", preferred_window="morning")
    bath = make_task("Bath")

    ordered = Scheduler(make_owner()).sort_by_time([bath, play, walk, meds])

    assert [t.title for t in ordered] == ["Walk", "Meds", "Play", "Bath"]


def test_fixed_time_accepts_hhmm_strings():
    assert make_task("Meds", fixed_time="7:30").fixed_time == time(7, 30)
    with pytest.raises(ValueError):
        make_task("Meds", fixed_time="half past seven")


def test_sort_by_time_handles_tasks_added_out_of_order():
    tasks = [make_task(t, fixed_time=hhmm) for t, hhmm in
             [("Dinner", "18:00"), ("Meds", "7:30"), ("Lunch", "12:15"), ("Late walk", "21:00")]]

    ordered = Scheduler(make_owner()).sort_by_time(tasks)

    assert [t.title for t in ordered] == ["Meds", "Lunch", "Dinner", "Late walk"]


def test_flexible_task_is_placed_inside_its_window():
    owner = make_owner()
    owner.get_pet("Luna").add_task(make_task("Play", 20, "medium", preferred_window="evening"))

    item = plan_for(owner).scheduled_items[0]

    assert item.start_time == time(17, 0)
    assert "evening window" in item.reason


def test_fixed_task_starts_at_its_time_and_others_fill_gaps():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    mochi.add_task(make_task("Breakfast", 10, fixed_time=time(8, 0)))
    mochi.add_task(make_task("Walk", 30))

    items = plan_for(owner).scheduled_items

    assert [(i.task.title, i.start_time) for i in items] == [
        ("Breakfast", time(8, 0)),
        ("Walk", time(8, 10)),
    ]


def test_fixed_task_outside_day_is_unscheduled():
    owner = make_owner(start=time(9, 0))
    owner.get_pet("Mochi").add_task(make_task("Early meds", 5, fixed_time=time(7, 0)))

    plan = plan_for(owner)

    assert plan.scheduled_items == []
    assert "outside your day" in plan.unscheduled_items[0][1]


# --- Filtering ---

def test_filter_tasks_by_pet_and_status():
    owner = make_owner()
    walk = make_task("Walk")
    owner.get_pet("Mochi").add_task(walk)
    owner.get_pet("Luna").add_task(make_task("Play"))
    walk.mark_complete(DAY)

    assert [t.title for _, t in owner.filter_tasks(pet_name="luna")] == ["Play"]
    assert [t.title for _, t in owner.filter_tasks(completed=True)] == ["Walk"]
    assert [t.title for _, t in owner.filter_tasks(completed=False)] == ["Play"]


def test_filter_tasks_returns_pet_with_task():
    owner = make_owner()
    owner.get_pet("Luna").add_task(make_task("Play", priority="low"))

    [(pet, task)] = owner.filter_tasks(priority="low")

    assert pet.name == "Luna" and task.title == "Play"


# --- Recurring tasks ---

def test_completing_daily_task_creates_tomorrows_copy():
    pet = Pet("Mochi", "dog")
    walk = make_task("Walk", recurrence="daily")
    pet.add_task(walk)

    next_walk = pet.complete_task(walk.id, DAY)

    assert walk.completed and walk.completed_on == DAY
    assert next_walk in pet.tasks
    assert next_walk.due_date == DAY + timedelta(days=1)
    assert next_walk.id != walk.id and not next_walk.completed


def test_weekly_task_next_due_in_seven_days():
    brush = make_task("Brush", recurrence="weekly")
    assert brush.mark_complete(DAY).due_date == DAY + timedelta(weeks=1)


def test_overdue_daily_task_next_due_is_today_plus_one():
    late_walk = make_task("Walk", recurrence="daily", due_date=DAY - timedelta(days=3))
    assert late_walk.mark_complete(DAY).due_date == DAY + timedelta(days=1)


def test_scheduler_mark_task_complete_finds_pet_and_adds_next():
    owner = make_owner()
    meds = make_task("Meds", recurrence="daily")
    owner.get_pet("Luna").add_task(meds)

    next_meds = Scheduler(owner).mark_task_complete(meds.id, DAY)

    assert meds.completed
    assert next_meds in owner.get_pet("Luna").tasks
    assert next_meds.due_date == DAY + timedelta(days=1)
    assert (next_meds.title, next_meds.duration_minutes, next_meds.priority) == ("Meds", 10, Priority.HIGH)


def test_scheduler_mark_task_complete_unknown_id_raises():
    with pytest.raises(KeyError):
        Scheduler(make_owner()).mark_task_complete("nope")


def test_one_off_task_has_no_next_occurrence():
    pet = Pet("Mochi", "dog")
    bath = make_task("Bath")
    pet.add_task(bath)

    assert pet.complete_task(bath.id, DAY) is None
    assert len(pet.tasks) == 1


def test_completing_twice_does_not_duplicate():
    pet = Pet("Mochi", "dog")
    walk = make_task("Walk", recurrence="daily")
    pet.add_task(walk)

    pet.complete_task(walk.id, DAY)
    pet.complete_task(walk.id, DAY)

    assert len(pet.tasks) == 2


def test_scheduler_only_includes_tasks_due_today():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    walk = make_task("Walk", recurrence="daily")
    mochi.add_task(walk)
    mochi.add_task(make_task("Vet", due_date=DAY + timedelta(days=3)))
    mochi.complete_task(walk.id, DAY)

    assert plan_for(owner).scheduled_items == []
    tomorrow = Scheduler(owner).generate_plan(DAY + timedelta(days=1))
    assert [i.task.title for i in tomorrow.scheduled_items] == ["Walk"]


# --- Conflict detection ---

def test_overlapping_fixed_tasks_for_different_pets_warn_owner():
    owner = make_owner()
    owner.get_pet("Mochi").add_task(make_task("Breakfast", 10, fixed_time=time(8, 0)))
    owner.get_pet("Luna").add_task(make_task("Meds", 5, fixed_time=time(8, 0)))

    plan = plan_for(owner)

    assert len(plan.scheduled_items) == 2
    assert any("You're double-booked" in w for w in plan.warnings)


def test_check_conflicts_same_time_different_pets():
    owner = make_owner()
    owner.get_pet("Mochi").add_task(make_task("Breakfast", 10, fixed_time="07:30"))
    owner.get_pet("Luna").add_task(make_task("Meds", 5, fixed_time="07:30"))

    [warning] = Scheduler(owner).check_conflicts(DAY)

    assert "You're double-booked" in warning and "Breakfast" in warning and "Meds" in warning


def test_check_conflicts_same_pet():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    mochi.add_task(make_task("Walk", 30, fixed_time="09:00"))
    mochi.add_task(make_task("Vet call", 10, fixed_time="09:15"))

    [warning] = Scheduler(owner).check_conflicts(DAY)

    assert warning.startswith("Mochi is double-booked")


def test_check_conflicts_ignores_back_to_back_done_and_future_tasks():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    mochi.add_task(make_task("Walk", 30, fixed_time="09:00"))
    mochi.add_task(make_task("Feed", 10, fixed_time="09:30"))              # starts as Walk ends
    done = make_task("Old meds", 5, fixed_time="09:00")
    mochi.add_task(done)
    done.mark_complete(DAY)                                                 # already done
    mochi.add_task(make_task("Groom", 15, fixed_time="09:00", due_date=DAY + timedelta(days=2)))

    assert Scheduler(owner).check_conflicts(DAY) == []


def test_conflicts_return_warnings_instead_of_raising():
    owner = make_owner()
    for pet in owner.pets:
        pet.add_task(make_task("Same time", 20, fixed_time="08:00"))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(DAY)

    assert len(plan.scheduled_items) == 2
    assert plan.warnings and scheduler.check_conflicts(DAY)


def test_overlap_for_same_pet_names_the_pet():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    mochi.add_task(make_task("Walk", 60, fixed_time=time(9, 0)))
    mochi.add_task(make_task("Groom", 15, fixed_time=time(9, 30)))

    assert any("Mochi is double-booked" in w for w in plan_for(owner).warnings)


def test_long_task_overlapping_two_later_tasks_reports_both():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    mochi.add_task(make_task("Hike", 120, fixed_time=time(9, 0)))
    mochi.add_task(make_task("A", 10, fixed_time=time(9, 30)))
    mochi.add_task(make_task("B", 10, fixed_time=time(10, 30)))

    overlaps = [w for w in plan_for(owner).warnings if "double-booked" in w]

    assert len(overlaps) == 2


def test_back_to_back_tasks_do_not_conflict():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    mochi.add_task(make_task("Walk", 30))
    mochi.add_task(make_task("Feed", 10))

    assert plan_for(owner).warnings == []


def test_duplicate_titles_for_same_pet_warn():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    mochi.add_task(make_task("Feeding"))
    mochi.add_task(make_task("feeding "))

    assert any("Possible duplicate" in w for w in plan_for(owner).warnings)


def test_window_with_no_room_falls_back_and_warns():
    owner = make_owner(start=time(8, 0), end=time(20, 0))
    # Fills the whole evening up to day end (17:00-20:00), leaving no room for Play.
    owner.get_pet("Mochi").add_task(make_task("Long hike", 180, fixed_time=time(17, 0)))
    owner.get_pet("Luna").add_task(make_task("Play", 30, "medium", preferred_window="evening"))

    plan = plan_for(owner)
    play = next(i for i in plan.scheduled_items if i.task.title == "Play")

    assert play.start_time == time(8, 0)
    assert any("outside its preferred evening window" in w for w in plan.warnings)


# --- FreeTime ---

def test_free_time_reserve_splits_gap_and_charges_budget():
    free = FreeTime(480, 720, budget=100)      # 08:00-12:00

    free.reserve(540, 30)                      # 09:00-09:30

    assert free.gaps == [(480, 540), (570, 720)]
    assert free.remaining == 70


def test_free_time_find_respects_window_and_gaps():
    free = FreeTime(360, 1200, budget=600)     # 06:00-20:00
    free.reserve(1020, 170)                    # 17:00-19:50 taken

    assert free.find(30) == 360                # any time: first gap
    assert free.find(30, "afternoon") == 720   # 12:00, start of window
    assert free.find(30, "evening") is None    # only 10 min left in evening


# --- Time budget ---

def test_skip_reason_says_how_many_minutes_short():
    owner = make_owner(minutes=40)
    owner.get_pet("Mochi").add_task(make_task("Bath", 45, "low"))

    [(task, reason)] = plan_for(owner).unscheduled_items

    assert reason == "needs 45 min, only 40 left (5 short)"


def test_smaller_task_still_fits_after_larger_one_is_skipped():
    owner = make_owner(minutes=30)
    mochi = owner.get_pet("Mochi")
    mochi.add_task(make_task("Bath", 45, "low"))
    mochi.add_task(make_task("Brush", 15, "low"))

    plan = plan_for(owner)

    assert [i.task.title for i in plan.scheduled_items] == ["Brush"]
    assert [t.title for t, _ in plan.unscheduled_items] == ["Bath"]


def test_invalid_fixed_time_past_midnight_rejected():
    with pytest.raises(ValueError):
        make_task("Late", 30, fixed_time=time(23, 45))
