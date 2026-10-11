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

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

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
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

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

- The scheduler uses `due_on` to plan only the tasks due that day. The app's "Show pet" / "Show status" filters call the same method.

### Conflict detection

- **`Scheduler.check_conflicts(on_date)`** is a lightweight check that runs without building a plan. It looks at tasks pinned to an exact time and warns about any that overlap. The app runs it as soon as a task is added.
- **`Scheduler.detect_conflicts(items)`** runs on the finished plan and also flags tasks placed outside their preferred window and likely duplicates (same pet and title).
- Overlaps compare **full durations**, not just start times, using `ScheduledItem.overlaps()`. So 07:30–07:40 and 07:35–07:50 conflict, but back-to-back tasks don't. Every pair is checked, which is O(n²) but instant at the size of a day's task list.
- Both return **warning strings instead of raising**, so the plan is still built:
  - `You're double-booked: 'Breakfast' for Mochi (07:30-07:40) overlaps 'Kidney meds' for Luna (07:30-07:35)`
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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
