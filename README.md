# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## ✨ Features

### Planning

- **Priority-first scheduling:** builds the day greedily, high → medium → low priority, shortest first within a priority. A higher-priority task is never dropped to make room for a lower one.
- **Exact times and preferred windows:** tasks can be pinned to an exact time (`"7:30"`) or prefer morning, afternoon or evening. Pinned tasks are placed first, then the rest go in the earliest free gap inside their window, or the first free gap anywhere if the window is full.
- **Time budget:** uses the smaller of the owner's available minutes and the length of their day, and stops once that budget runs out.
- **Explained decisions:** every scheduled or skipped task gets a one-line reason, e.g. `high priority meds, fixed at 07:30` or `needs 45 min, only 15 left (30 short)`.

### Organizing tasks

- **Sorting by time:** lists tasks in clock order by exact time or window start, with untimed tasks last and ties broken by priority. Times are compared as times, not text, so `7:30` comes before `12:15`.
- **Sorting by priority:** high → low, then shorter duration, then title.
- **Filtering:** by pet, completion status, priority, category or due date, combined freely (e.g. "Luna's high-priority tasks still to do").

### Recurring tasks

- **Daily and weekly recurrence:** completing a recurring task automatically creates the next one, due **today + 1 day** (daily) or **+ 7 days** (weekly). This holds across month, year and leap-day boundaries.
- **Overdue carry-over:** unfinished tasks stay on the schedule until done, and future tasks wait until their due date.
- **History kept:** the completed task stays in the list, and completing it twice never creates a duplicate.

### Conflict warnings

- **Overlap detection:** flags tasks whose times overlap across their full durations, not just matching start times. Back-to-back tasks don't count.
- **Same pet vs. different pets:** "Mochi is double-booked…" vs. "You're double-booked…" (you can't be in two places at once).
- **Warns, never blocks:** conflicts appear as warnings and the plan is still built. The app shows them as soon as a clashing task is added.
- **Plan checks:** also flags tasks placed outside their preferred window and likely duplicates (same pet, same title).

See [📐 Smarter Scheduling](#-smarter-scheduling) for the method behind each feature.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output


```
└─[$]> python3 main.py
============================================================
Today's Schedule for Jordan's pets (Sunday, October 11)
============================================================
07:00-07:05  Kidney meds    Luna     5 min  [high]
             why: high priority meds
07:05-07:15  Breakfast      Mochi   10 min  [high]
             why: high priority feeding
07:15-07:45  Morning walk   Mochi   30 min  [high]
             why: high priority exercise, prefers morning
07:45-08:05  Laser play     Luna    20 min  [medium]
             why: medium priority exercise
08:05-08:20  Brushing       Luna    15 min  [low]
             why: low priority grooming

Skipped today:
  - Bath (45 min): needs 45 min but not enough time left after higher-priority tasks
------------------------------------------------------------
Time used: 80 / 120 min (40 min free)
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest -v

# Run with coverage:
pytest --cov
```

Sample test output:

```
 python -m pytest -v
=================================================================================================================== test session starts ====================================================================================================================
platform darwin -- Python 3.13.5, pytest-8.3.4, pluggy-1.5.0 -- /opt/anaconda3/bin/python
cachedir: .pytest_cache
rootdir: /Users/leeafeawo/Projects/ai110-module2show-pawpal-starter
plugins: anyio-4.7.0
collected 53 items                                                                                                                                                                                                                                         

tests/test_pawpal.py::test_mark_complete_changes_status PASSED                                                                                                                                                                                       [  1%]
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED                                                                                                                                                                                  [  3%]
tests/test_pawpal.py::test_task_ids_are_generated_and_unique PASSED                                                                                                                                                                                  [  5%]
tests/test_pawpal.py::test_sort_by_time_orders_fixed_then_window_then_untimed PASSED                                                                                                                                                                 [  7%]
tests/test_pawpal.py::test_fixed_time_accepts_hhmm_strings PASSED                                                                                                                                                                                    [  9%]
tests/test_pawpal.py::test_sort_by_time_handles_tasks_added_out_of_order PASSED                                                                                                                                                                      [ 11%]
tests/test_pawpal.py::test_flexible_task_is_placed_inside_its_window PASSED                                                                                                                                                                          [ 13%]
tests/test_pawpal.py::test_fixed_task_starts_at_its_time_and_others_fill_gaps PASSED                                                                                                                                                                 [ 15%]
tests/test_pawpal.py::test_fixed_task_outside_day_is_unscheduled PASSED                                                                                                                                                                              [ 16%]
tests/test_pawpal.py::test_filter_tasks_by_pet_and_status PASSED                                                                                                                                                                                     [ 18%]
tests/test_pawpal.py::test_filter_tasks_returns_pet_with_task PASSED                                                                                                                                                                                 [ 20%]
tests/test_pawpal.py::test_completing_daily_task_creates_tomorrows_copy PASSED                                                                                                                                                                       [ 22%]
tests/test_pawpal.py::test_weekly_task_next_due_in_seven_days PASSED                                                                                                                                                                                 [ 24%]
tests/test_pawpal.py::test_overdue_daily_task_next_due_is_today_plus_one PASSED                                                                                                                                                                      [ 26%]
tests/test_pawpal.py::test_scheduler_mark_task_complete_finds_pet_and_adds_next PASSED                                                                                                                                                               [ 28%]
tests/test_pawpal.py::test_scheduler_mark_task_complete_unknown_id_raises PASSED                                                                                                                                                                     [ 30%]
tests/test_pawpal.py::test_one_off_task_has_no_next_occurrence PASSED                                                                                                                                                                                [ 32%]
tests/test_pawpal.py::test_completing_twice_does_not_duplicate PASSED                                                                                                                                                                                [ 33%]
tests/test_pawpal.py::test_scheduler_only_includes_tasks_due_today PASSED                                                                                                                                                                            [ 35%]
tests/test_pawpal.py::test_overlapping_fixed_tasks_for_different_pets_warn_owner PASSED                                                                                                                                                              [ 37%]
tests/test_pawpal.py::test_check_conflicts_same_time_different_pets PASSED                                                                                                                                                                           [ 39%]
tests/test_pawpal.py::test_check_conflicts_same_pet PASSED                                                                                                                                                                                           [ 41%]
tests/test_pawpal.py::test_check_conflicts_ignores_back_to_back_done_and_future_tasks PASSED                                                                                                                                                         [ 43%]
tests/test_pawpal.py::test_conflicts_return_warnings_instead_of_raising PASSED                                                                                                                                                                       [ 45%]
tests/test_pawpal.py::test_overlap_for_same_pet_names_the_pet PASSED                                                                                                                                                                                 [ 47%]
tests/test_pawpal.py::test_long_task_overlapping_two_later_tasks_reports_both PASSED                                                                                                                                                                 [ 49%]
tests/test_pawpal.py::test_back_to_back_tasks_do_not_conflict PASSED                                                                                                                                                                                 [ 50%]
tests/test_pawpal.py::test_duplicate_titles_for_same_pet_warn PASSED                                                                                                                                                                                 [ 52%]
tests/test_pawpal.py::test_window_with_no_room_falls_back_and_warns PASSED                                                                                                                                                                           [ 54%]
tests/test_pawpal.py::test_free_time_reserve_splits_gap_and_charges_budget PASSED                                                                                                                                                                    [ 56%]
tests/test_pawpal.py::test_free_time_find_respects_window_and_gaps PASSED                                                                                                                                                                            [ 58%]
tests/test_pawpal.py::test_skip_reason_says_how_many_minutes_short PASSED                                                                                                                                                                            [ 60%]
tests/test_pawpal.py::test_smaller_task_still_fits_after_larger_one_is_skipped PASSED                                                                                                                                                                [ 62%]
tests/test_pawpal.py::test_invalid_fixed_time_past_midnight_rejected PASSED                                                                                                                                                                          [ 64%]
tests/test_pawpal.py::test_sort_same_exact_time_breaks_tie_by_priority PASSED                                                                                                                                                                        [ 66%]
tests/test_pawpal.py::test_sort_empty_list_returns_empty PASSED                                                                                                                                                                                      [ 67%]
tests/test_pawpal.py::test_daily_task_rolls_over_to_new_year PASSED                                                                                                                                                                                  [ 69%]
tests/test_pawpal.py::test_weekly_task_crosses_leap_day PASSED                                                                                                                                                                                       [ 71%]
tests/test_pawpal.py::test_completed_early_next_due_counts_from_due_date PASSED                                                                                                                                                                      [ 73%]
tests/test_pawpal.py::test_next_occurrence_keeps_time_window_and_details PASSED                                                                                                                                                                      [ 75%]
tests/test_pawpal.py::test_pet_with_no_tasks_gives_empty_plan PASSED                                                                                                                                                                                 [ 77%]
tests/test_pawpal.py::test_owner_with_no_pets_gives_empty_plan PASSED                                                                                                                                                                                [ 79%]
tests/test_pawpal.py::test_fixed_task_ending_exactly_at_day_end_is_scheduled PASSED                                                                                                                                                                  [ 81%]
tests/test_pawpal.py::test_fixed_task_one_minute_past_day_end_is_skipped PASSED                                                                                                                                                                      [ 83%]
tests/test_pawpal.py::test_high_priority_beats_low_when_time_is_short PASSED                                                                                                                                                                         [ 84%]
tests/test_pawpal.py::test_same_priority_shorter_task_goes_first PASSED                                                                                                                                                                              [ 86%]
tests/test_pawpal.py::test_daily_budget_is_smaller_of_minutes_and_day_length PASSED                                                                                                                                                                  [ 88%]
tests/test_pawpal.py::test_zero_budget_skips_everything_without_crashing PASSED                                                                                                                                                                      [ 90%]
tests/test_pawpal.py::test_update_rolls_back_when_change_is_invalid PASSED                                                                                                                                                                           [ 92%]
tests/test_pawpal.py::test_update_rejects_unknown_fields_and_id PASSED                                                                                                                                                                               [ 94%]
tests/test_pawpal.py::test_edit_task_applies_valid_change PASSED                                                                                                                                                                                     [ 96%]
tests/test_pawpal.py::test_edit_or_remove_missing_task_raises_keyerror PASSED                                                                                                                                                                        [ 98%]
tests/test_pawpal.py::test_owner_rejects_bad_constraints_and_duplicate_pet_names PASSED                                                                                                                                                              [100%]

==================================================================================================================== 53 passed in 0.03s ===================================================================================================
```
Confidence Level ⭐️⭐️⭐️⭐️⭐️

## 📐 Smarter Scheduling

All scheduling logic lives in [`pawpal_system.py`](pawpal_system.py). Each feature is covered by tests in [`tests/test_pawpal.py`](tests/test_pawpal.py) and demonstrated in [`main.py`](main.py).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Task.sort_key()`, `Scheduler.rank_tasks()` | Clock order by time; priority order for scheduling |
| Filtering | `Owner.filter_tasks()` | By pet, completion status, category, priority, due date |
| Conflict handling | `Scheduler.check_conflicts()`, `Scheduler.detect_conflicts()` | Overlapping durations, same or different pets; warns, never crashes |
| Recurring tasks | `Task.mark_complete()`, `Pet.complete_task()`, `Scheduler.mark_task_complete()`, `Task.is_due()` | Daily → next due today + 1 day; weekly → + 7 days |
| Time placement | `Scheduler.generate_plan()`, `FreeTime.find()`, `FreeTime.reserve()` | Fixed times first, then preferred windows, then any free gap |

### Sorting

- **`Scheduler.sort_by_time(tasks)`** returns tasks in clock order. A task's time is its exact `fixed_time` (e.g. `"7:30"`), otherwise the start of its preferred window (morning 06:00, afternoon 12:00, evening 17:00). Tasks with no time go last.
- It uses `sorted()` with a tuple key, `(has no time, time, sort_key)`, so ties at the same time fall back to priority. Times are stored as `datetime.time`, not strings, so `"7:30"` correctly sorts before `"12:15"`.
- **`Task.sort_key()`** ranks tasks for scheduling: priority (high → low), then shorter duration, then title. **`Scheduler.rank_tasks()`** sorts a list by this key.

### Filtering

- **`Owner.filter_tasks(pet_name=None, completed=None, category=None, priority=None, due_on=None)`** returns `(pet, task)` pairs. Filters combine with AND, and any filter left as `None` is ignored.

```python
owner.filter_tasks(pet_name="Luna")                                  # one pet
owner.filter_tasks(completed=False)                                  # still to do
owner.filter_tasks(pet_name="Mochi", completed=False, due_on=today)  # combined
```

- The scheduler uses `due_on` to plan only the tasks due that day. The app's Pet / Status / Priority filters call the same method, and its "Sort by" menu uses `sort_by_time()` or `rank_tasks()`.

### Conflict detection

- **`Scheduler.check_conflicts(on_date)`** is a lightweight check that runs without building a plan. It looks at tasks pinned to an exact time inside the owner's day (`Scheduler.within_day()`) and warns about any that overlap. The app runs it as soon as a task is added.
- **`Scheduler.detect_conflicts(items)`** runs on the finished plan and also flags tasks placed outside their preferred window and likely duplicates (same pet and title).
- Overlaps compare **full durations**, not just start times, using `ScheduledItem.overlaps()`. So 07:30–07:40 and 07:35–07:50 conflict, but back-to-back tasks don't. Every pair is checked, which is O(n²) but instant at the size of a day's task list.
- Both return **warning strings instead of raising**, so the plan is still built:
  - `You're double-booked: 'Kidney meds' for Luna (07:30-07:35) overlaps 'Breakfast' for Mochi (07:30-07:40)`
  - `Mochi is double-booked: 'Breakfast' (07:30-07:40) and 'Vet call' (07:35-07:50)`

### Recurring tasks

- Each task has a `recurrence` (`None`, `"daily"`, `"weekly"`) and a `due_date`.
- **`Task.mark_complete(on_date)`** marks the task done and, if it recurs, returns a copy with a new id due one step later. The step is counted from the later of the due date and the completion date, so a daily task completed today, even if overdue, is next due **today + 1 day**. Completing an already-completed task does nothing, so no duplicate copies are created.
- **`Pet.complete_task(task_id)`** adds that next copy to the pet. **`Scheduler.mark_task_complete(task_id)`** does the same without needing to know which pet owns the task. The app's "Mark complete" button uses this.
- **`Task.is_due(date)`** decides what gets scheduled. Unfinished tasks carry over as overdue, and future ones wait until their date.

### Time placement

- **`Scheduler.generate_plan(plan_date)`** is greedy and runs in two passes:
  1. Fixed-time tasks are placed exactly at their time.
  2. Flexible tasks are placed by rank in the earliest free gap inside their preferred window, falling back to any free gap, or skipped if none fits.
- **`FreeTime`** tracks the day's free gaps and the remaining time budget. `find()` locates the first gap that fits, and `reserve()` takes it.
- Every decision gets a one-line reason built from an **`Outcome`** template, e.g. `needs 45 min, only 15 left (30 short)`.
- Tradeoff: higher-priority tasks are never bumped to fit lower-priority ones, even if that leaves some time unused. See [reflection.md](reflection.md), section 2b.

## 📸 Demo Walkthrough

Run the app with `python -m streamlit run app.py` (it opens at <http://localhost:8501>). Data lives in the browser session, so refreshing the tab starts fresh.

Follow these numbered steps to try the main workflow (add pets → schedule tasks → view today's schedule):

1. **Set up your day.** Under **Owner**, set *Available minutes* to 120, *Day starts* to 07:00 and *Day ends* to 21:00.
2. **Add pets.** Add **Mochi** (dog), then **Luna** (cat, special needs "kidney diet"). Both appear in the Pets table with 0 tasks.
3. **Add a fixed-time task.** For Mochi, add *Breakfast*: 10 min, high priority, category feeding, exact time 07:30, repeats daily.
4. **Trigger a conflict.** For Luna, add *Kidney meds*: 5 min, high, exact time 07:30, daily. A warning appears right away: *You're double-booked: 'Kidney meds' for Luna (07:30-07:35) overlaps 'Breakfast' for Mochi (07:30-07:40)*.
5. **Add flexible tasks.** For Mochi, add *Morning walk* (30 min, high, preferred time morning, daily). For Luna, add *Laser play* (20 min, medium, preferred time evening).
6. **Sort and filter.** With *Sort by: Time of day*, the list reads Morning walk (Morning) → Kidney meds and Breakfast (07:30) → Laser play (Evening). Set *Pet* to Luna to see only her tasks.
7. **View today's schedule.** Click **Generate schedule**. Morning walk lands at 07:00 in its morning window, the two 07:30 tasks stay at 07:30, and Laser play waits until 17:00. The metrics show 4 scheduled and 65 min used, and the plan points back to the time conflict.
8. **Complete a recurring task.** Choose *Breakfast (Mochi…)* and click **Mark complete**. The app confirms *Done! Next 'Breakfast' is due* tomorrow. Set *Status* to Done to see it checked off, or To do to see tomorrow's copy waiting.

### Main UI features

| Section | What you can do |
|---|---|
| **Owner** | Set your name, available minutes for the day, and when your day starts and ends. Invalid hours (start after end) show an error. |
| **Pets** | Add a pet with name, species, age and optional special needs. A table lists your pets and how many tasks each has. Duplicate names are rejected. |
| **Tasks: add** | Pick a pet, then set title, duration, priority, category, preferred time (morning / afternoon / evening), an optional exact time, and whether it repeats (daily / weekly). |
| **Tasks: conflicts** | A ⚠️ warning appears as soon as two exact-time tasks overlap, before you build a schedule. |
| **Tasks: mark complete** | Choose a task and click **Mark complete**. Recurring tasks report when the next one is due. |
| **Tasks: list** | Filter by **Pet**, **Status** (All / To do / Done) and **Priority**, and **Sort by** time of day, priority, or date added. |
| **Build Schedule** | Click **Generate schedule** to see summary metrics (scheduled, skipped, time used, free), a budget bar, the day's plan with a reason for each task, skipped tasks with reasons, and any warnings. |

### Key Scheduler behaviors shown

- **Sorting by time** (`Scheduler.sort_by_time()`): exact times and window starts in clock order, with untimed tasks last.
- **Priority-first placement** (`Scheduler.generate_plan()`): exact-time tasks are pinned first, then the rest are placed by priority in their preferred window.
- **Conflict warnings** (`Scheduler.check_conflicts()`, `detect_conflicts()`): overlapping durations are flagged for the same pet or different pets, and the plan is still built.
- **Daily and weekly recurrence** (`Scheduler.mark_task_complete()`): completing a task creates the next one, due today + 1 day (daily) or + 7 days (weekly).
- **Filtering** (`Owner.filter_tasks()`): by pet, status and priority, combined.
- **Budget and explanations:** tasks that don't fit are skipped with exactly how many minutes they were short.

### Sample CLI output

`python main.py` runs the same logic in the terminal. It adds tasks out of order, then sorts, filters, checks for conflicts, schedules, completes the morning's tasks, and plans tomorrow. An excerpt (dates depend on when you run it):

```text
============================================================
2. Sorted by time with Scheduler.sort_by_time()
============================================================
      Morning walk   Mochi  morning
      Kidney meds    Luna   at 07:30
      Breakfast      Mochi  at 07:30
      Lunch meds     Luna   at 12:15
      Laser play     Luna   evening
      Evening walk   Mochi  evening
      Dinner         Luna   at 18:00
      Brushing       Luna   any time
      Bath           Mochi  any time

============================================================
3b. Conflict check (before scheduling)
============================================================
  ⚠ You're double-booked: 'Kidney meds' for Luna (07:30-07:35) overlaps 'Breakfast' for Mochi (07:30-07:40)
  ⚠ Mochi is double-booked: 'Breakfast' (07:30-07:40) and 'Vet call' (07:35-07:50)

============================================================
4. Today's Schedule (Sunday, October 11)
============================================================
Plan for 2026-10-11
Scheduled:
  07:00-07:30  Morning walk (Mochi, 30 min, high) - high priority exercise, in its morning window
  07:30-07:35  Kidney meds (Luna, 5 min, high) - high priority meds, fixed at 07:30
  07:30-07:40  Breakfast (Mochi, 10 min, high) - high priority feeding, fixed at 07:30
  07:35-07:50  Vet call (Mochi, 15 min, high) - high priority, fixed at 07:35
  07:50-08:05  Brushing (Luna, 15 min, low) - low priority grooming
  12:15-12:20  Lunch meds (Luna, 5 min, high) - high priority meds, fixed at 12:15
  17:00-17:20  Laser play (Luna, 20 min, medium) - medium priority exercise, in its evening window
  17:20-17:50  Evening walk (Mochi, 30 min, medium) - medium priority exercise, in its evening window
  18:00-18:05  Dinner (Luna, 5 min, high) - high priority feeding, fixed at 18:00
Not scheduled:
  Bath (45 min) - needs 45 min, only 15 left (30 short)
Warnings:
  You're double-booked: 'Kidney meds' for Luna (07:30-07:35) overlaps 'Breakfast' for Mochi (07:30-07:40)
  Mochi is double-booked: 'Breakfast' (07:30-07:40) and 'Vet call' (07:35-07:50)
Total time: 135 min

============================================================
5. Complete this morning's tasks
============================================================
  ✓ Morning walk   next due 2026-10-12
  ✓ Kidney meds    next due 2026-10-12
  ✓ Breakfast      next due 2026-10-12
  ✓ Vet call       one-off, not repeated
  ✓ Brushing       next due 2026-10-18

============================================================
8. Filter combined: Mochi's tasks still to do today
============================================================
  [ ] Evening walk   Mochi  evening
  [ ] Bath           Mochi  any time
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

