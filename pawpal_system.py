"""PawPal+ core system: owners, pets, tasks, and the daily scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from datetime import date, datetime, time, timedelta
from enum import Enum
from itertools import combinations
from typing import Optional
from uuid import uuid4


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Outcome(Enum):
    """Why a task was or wasn't scheduled; each value is its reason template."""
    SCHEDULED = "{base}{window_note}"
    FIXED = "{base}, fixed at {fixed}"
    OUTSIDE_WINDOW = "{base}; no room in its {window} window, so placed at the first free time"
    NO_TIME = "needs {minutes} min, only {remaining} left ({short} short)"
    NO_SLOT = "needs {minutes} min but no free gap that long is left today"
    OUTSIDE_DAY = "fixed at {fixed}, outside your day ({day})"


# Lower rank sorts first.
PRIORITY_RANK = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}

# Named preferred windows as (start, end) times.
WINDOWS = {
    "morning": (time(6, 0), time(12, 0)),
    "afternoon": (time(12, 0), time(17, 0)),
    "evening": (time(17, 0), time(22, 0)),
}

RECURRENCES = {None, "none", "daily", "weekly"}
RECURRENCE_STEP = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}

LAST_MINUTE = 23 * 60 + 59


def to_minutes(t: time) -> int:
    """Convert a time of day to minutes since midnight."""
    return t.hour * 60 + t.minute


def from_minutes(m: int) -> time:
    """Convert minutes since midnight to a time of day."""
    return time(m // 60, m % 60)


def parse_hhmm(value: str) -> time:
    """Parse an 'HH:MM' string (e.g. '07:30' or '7:30') into a time."""
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError:
        raise ValueError(f"Time must be in HH:MM format, got {value!r}")


def new_id() -> str:
    """Return a new unique task id."""
    return uuid4().hex


class FreeTime:
    """The free gaps left in a day (in minutes since midnight) and the owner's remaining budget."""

    def __init__(self, day_start: int, day_end: int, budget: int) -> None:
        """Start with one gap covering the whole day and the full budget."""
        self.gaps = [(day_start, day_end)]
        self.remaining = budget

    def find(self, minutes: int, window: Optional[str] = None) -> Optional[int]:
        """Return the earliest start where `minutes` fit in a free gap (and window), or None.

        First-fit search: walk the gaps in time order and, for each one, clip it to the
        window (start no earlier than the window opens, end no later than it closes).
        The first clipped gap long enough wins. O(g) for g gaps.

        Args:
            minutes: Length of the task to place.
            window: A key of WINDOWS (e.g. "evening"), or None for any time of day.

        Returns:
            Start time in minutes since midnight, or None if nothing fits.
        """
        win_start, win_end = (to_minutes(t) for t in WINDOWS[window]) if window else (0, 24 * 60)
        for gap_start, gap_end in self.gaps:
            start = max(gap_start, win_start)
            if start + minutes <= min(gap_end, win_end):
                return start
        return None

    def reserve(self, start: int, minutes: int) -> None:
        """Remove [start, start + minutes) from the free gaps and charge it to the budget.

        Each gap keeps whatever part lies before `start` and whatever part lies after
        the end, so a gap the task sits inside is split in two, and a gap the task
        covers completely disappears. Works even if the range is already partly taken
        (overlapping fixed-time tasks). O(g) for g gaps.

        Args:
            start: Start in minutes since midnight.
            minutes: Length to reserve; also subtracted from `remaining`.
        """
        end = start + minutes
        new_gaps = []
        for gap_start, gap_end in self.gaps:
            if gap_start < start:
                new_gaps.append((gap_start, min(gap_end, start)))
            if gap_end > end:
                new_gaps.append((max(gap_start, end), gap_end))
        self.gaps = new_gaps
        self.remaining -= minutes


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    category: Optional[str] = None          # feeding, exercise, meds, grooming
    preferred_window: Optional[str] = None  # a key of WINDOWS, e.g. "morning"
    fixed_time: Optional[time] = None       # must start exactly at this time
    recurrence: Optional[str] = None        # none, daily, weekly
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    completed_on: Optional[date] = None
    id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        """Convert string priority and 'HH:MM' fixed time, then validate the new task."""
        # Accept "high"/"medium"/"low" strings for convenience (e.g. from the UI).
        if isinstance(self.priority, str):
            try:
                self.priority = Priority(self.priority.lower())
            except ValueError:
                raise ValueError(f"Invalid priority: {self.priority!r}")
        if isinstance(self.fixed_time, str):
            self.fixed_time = parse_hhmm(self.fixed_time)
        self.validate()

    def validate(self) -> None:
        """Raise ValueError if any field holds an invalid value."""
        if not self.title or not self.title.strip():
            raise ValueError("Task title cannot be empty")
        if not isinstance(self.duration_minutes, int) or self.duration_minutes <= 0:
            raise ValueError(f"Duration must be a positive integer, got {self.duration_minutes!r}")
        if not isinstance(self.priority, Priority):
            raise ValueError(f"Invalid priority: {self.priority!r}")
        if self.preferred_window is not None and self.preferred_window not in WINDOWS:
            raise ValueError(
                f"Invalid preferred window {self.preferred_window!r}; choose from {sorted(WINDOWS)}"
            )
        if self.fixed_time is not None:
            if not isinstance(self.fixed_time, time):
                raise ValueError(f"Fixed time must be a time, got {self.fixed_time!r}")
            if to_minutes(self.fixed_time) + self.duration_minutes > LAST_MINUTE:
                raise ValueError(f"'{self.title}' at {self.fixed_time:%H:%M} would run past midnight")
        if self.recurrence not in RECURRENCES:
            raise ValueError(f"Invalid recurrence: {self.recurrence!r}")
        if not isinstance(self.due_date, date):
            raise ValueError(f"Due date must be a date, got {self.due_date!r}")

    def is_due(self, on_date: date) -> bool:
        """Return True if the task is not completed and is due on or before on_date."""
        return not self.completed and self.due_date <= on_date

    def mark_complete(self, on_date: Optional[date] = None) -> Optional[Task]:
        """Mark this task completed; for a recurring task, return its next occurrence.

        The next occurrence is a copy (via dataclasses.replace) with a new id, not
        completed, and due one step after the later of the due date and the completion
        date: so a daily task done today, even if overdue, is next due today + 1 day.
        The original stays completed as history. Calling this on an already-completed
        task does nothing, so a task can't spawn duplicate copies.

        Args:
            on_date: Completion date; defaults to today.

        Returns:
            The next Task for "daily"/"weekly" tasks, otherwise None. The caller adds it
            to a pet (see Pet.complete_task).
        """
        if self.completed:
            return None
        self.completed = True
        self.completed_on = on_date or date.today()

        step = RECURRENCE_STEP.get(self.recurrence)
        if step is None:
            return None
        # Count from the later of due date and completion, so an overdue task isn't due again at once.
        next_due = max(self.due_date, self.completed_on) + step
        return replace(self, id=new_id(), due_date=next_due, completed=False, completed_on=None)

    def update(self, **changes) -> None:
        """Apply field changes and re-validate, rolling back if the result is invalid."""
        allowed = {f.name for f in fields(self)} - {"id"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Cannot update field(s): {sorted(unknown)}")

        if isinstance(changes.get("priority"), str):
            changes["priority"] = Priority(changes["priority"].lower())
        if isinstance(changes.get("fixed_time"), str):
            changes["fixed_time"] = parse_hhmm(changes["fixed_time"])

        previous = {name: getattr(self, name) for name in changes}
        for name, value in changes.items():
            setattr(self, name, value)
        try:
            self.validate()
        except ValueError:
            for name, value in previous.items():
                setattr(self, name, value)
            raise

    def sort_key(self) -> tuple:
        """Return a sort key: priority first, then shorter duration, then title."""
        return (PRIORITY_RANK[self.priority], self.duration_minutes, self.title.lower())

    def earliest_start(self) -> Optional[time]:
        """Return the fixed time, else the preferred window's start, else None."""
        if self.fixed_time is not None:
            return self.fixed_time
        if self.preferred_window is not None:
            return WINDOWS[self.preferred_window][0]
        return None


@dataclass
class Pet:
    name: str
    species: str
    age: Optional[int] = None
    special_needs: Optional[str] = None
    tasks: list[Task] = field(default_factory=list)

    def _find_task(self, task_id: str) -> Task:
        """Return the task with the given id, or raise KeyError."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"{self.name} has no task with id {task_id!r}")

    def add_task(self, task: Task) -> None:
        """Add a task to this pet."""
        if any(t.id == task.id for t in self.tasks):
            raise ValueError(f"{self.name} already has a task with id {task.id!r}")
        task.validate()
        self.tasks.append(task)

    def edit_task(self, task_id: str, **changes) -> None:
        """Update the task with the given id."""
        self._find_task(task_id).update(**changes)

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id."""
        self.tasks.remove(self._find_task(task_id))

    def complete_task(self, task_id: str, on_date: Optional[date] = None) -> Optional[Task]:
        """Mark a task complete and add its next occurrence if it recurs."""
        next_task = self._find_task(task_id).mark_complete(on_date)
        if next_task is not None:
            self.tasks.append(next_task)
        return next_task

    def get_tasks(self, include_completed: bool = True) -> list[Task]:
        """Return this pet's tasks, optionally excluding completed ones."""
        if include_completed:
            return list(self.tasks)
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    available_minutes: int
    day_start: time = time(8, 0)
    day_end: time = time(20, 0)
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the owner's starting time constraints."""
        self._validate_constraints(self.available_minutes, self.day_start, self.day_end)

    @staticmethod
    def _validate_constraints(available_minutes: int, day_start: time, day_end: time) -> None:
        """Raise ValueError if minutes are negative or the day starts after it ends."""
        if available_minutes < 0:
            raise ValueError("Available minutes cannot be negative")
        if day_start >= day_end:
            raise ValueError("Day start must be before day end")

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"{self.name} already has a pet named {pet.name!r}")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove the pet with the given name."""
        pet = self.get_pet(pet_name)
        if pet is None:
            raise KeyError(f"{self.name} has no pet named {pet_name!r}")
        self.pets.remove(pet)

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Return the pet with the given name (case-insensitive), or None."""
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return pet
        return None

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        category: Optional[str] = None,
        priority: Optional[Priority | str] = None,
        due_on: Optional[date] = None,
    ) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs matching every filter that is not None.

        Filters combine with AND; any filter left as None is ignored, so calling with
        no arguments returns every task. Pairs keep pet order, then each pet's task
        order. One pass over all tasks: O(n).

        Args:
            pet_name: Only this pet's tasks (case-insensitive).
            completed: True for done tasks, False for not-done tasks.
            category: e.g. "meds".
            priority: A Priority or "high"/"medium"/"low".
            due_on: Only tasks not completed and due on or before this date.

        Returns:
            List of (Pet, Task) tuples, so callers always know whose task it is.
        """
        if isinstance(priority, str):
            priority = Priority(priority.lower())
        return [
            (pet, task)
            for pet in self.pets
            if pet_name is None or pet.name.lower() == pet_name.lower()
            for task in pet.tasks
            if (completed is None or task.completed == completed)
            and (category is None or task.category == category)
            and (priority is None or task.priority == priority)
            and (due_on is None or task.is_due(due_on))
        ]

    def get_all_tasks(self) -> list[Task]:
        """Return tasks across all of this owner's pets."""
        return [task for _, task in self.filter_tasks()]

    def set_constraints(self, available_minutes: int, day_start: time, day_end: time) -> None:
        """Update the owner's daily time budget and working hours."""
        self._validate_constraints(available_minutes, day_start, day_end)
        self.available_minutes = available_minutes
        self.day_start = day_start
        self.day_end = day_end

    def daily_budget(self) -> int:
        """Usable minutes today: the smaller of the time budget and the day's window."""
        window = to_minutes(self.day_end) - to_minutes(self.day_start)
        return min(self.available_minutes, window)


@dataclass
class ScheduledItem:
    task: Task
    pet: Pet
    start_time: time
    end_time: time
    reason: str

    @classmethod
    def starting_at(cls, pet: Pet, task: Task, start: time, reason: str = "") -> ScheduledItem:
        """Create an item for `task` starting at `start`, ending after its duration.

        Used for real placements in generate_plan and for "proposed" placements in
        check_conflicts, so the end-time math lives in one place.
        """
        end = from_minutes(to_minutes(start) + task.duration_minutes)
        return cls(task=task, pet=pet, start_time=start, end_time=end, reason=reason)

    def duration(self) -> int:
        """Return the length of this item in minutes."""
        return to_minutes(self.end_time) - to_minutes(self.start_time)

    def overlaps(self, other: ScheduledItem) -> bool:
        """Return True if this item's time range overlaps another's."""
        return self.start_time < other.end_time and other.start_time < self.end_time

    def span(self) -> str:
        """Return the time range as 'HH:MM-HH:MM'."""
        return f"{self.start_time:%H:%M}-{self.end_time:%H:%M}"


@dataclass
class Plan:
    date: date
    scheduled_items: list[ScheduledItem] = field(default_factory=list)
    unscheduled_items: list[tuple[Task, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def total_time_used(self) -> int:
        """Return total scheduled minutes."""
        return sum(item.duration() for item in self.scheduled_items)

    def time_remaining(self, available_minutes: int) -> int:
        """Return minutes left in the budget after scheduled items."""
        return max(0, available_minutes - self.total_time_used())

    def add_scheduled(self, item: ScheduledItem) -> None:
        """Add an item to the schedule."""
        self.scheduled_items.append(item)

    def add_unscheduled(self, task: Task, reason: str) -> None:
        """Record a task that could not be scheduled, with the reason."""
        self.unscheduled_items.append((task, reason))

    def summary(self) -> str:
        """Return a readable explanation of the day's plan."""
        lines = [f"Plan for {self.date.isoformat()}"]

        if self.scheduled_items:
            lines.append("Scheduled:")
            for item in self.scheduled_items:
                lines.append(
                    f"  {item.span()}  {item.task.title} ({item.pet.name}, "
                    f"{item.duration()} min, {item.task.priority.value}) - {item.reason}"
                )
        else:
            lines.append("Nothing scheduled.")

        if self.unscheduled_items:
            lines.append("Not scheduled:")
            for task, reason in self.unscheduled_items:
                lines.append(f"  {task.title} ({task.duration_minutes} min) - {reason}")

        if self.warnings:
            lines.append("Warnings:")
            lines.extend(f"  {w}" for w in self.warnings)

        lines.append(f"Total time: {self.total_time_used()} min")
        return "\n".join(lines)


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for the given owner's pets and tasks."""
        self.owner = owner

    def generate_plan(self, plan_date: Optional[date] = None) -> Plan:
        """Build a Plan: pin fixed-time tasks, then fit the rest into free gaps by priority.

        Greedy, two passes over the tasks due on `plan_date`:
          1. Fixed-time tasks are placed exactly at their time (in clock order), unless
             they fall outside the owner's day or exceed the time budget. Overlaps
             between them are allowed and reported as warnings, not errors.
          2. Flexible tasks are taken by rank (Task.sort_key: priority, then shorter
             first) and each goes in the earliest free gap inside its preferred window;
             if the window is full, the earliest free gap at all; otherwise it's skipped.
        Earlier decisions are never revisited, so a high-priority task is never bumped
        for a lower one (see reflection.md, 2b). O(n log n + n*g) for n tasks, g gaps.

        Args:
            plan_date: The day to plan; defaults to today.

        Returns:
            A Plan with items sorted by start time, skipped tasks with reasons, and
            warnings from detect_conflicts.
        """
        plan = Plan(date=plan_date or date.today())
        due = self.owner.filter_tasks(due_on=plan.date)
        day_start, day_end = to_minutes(self.owner.day_start), to_minutes(self.owner.day_end)
        free = FreeTime(day_start, day_end, self.owner.daily_budget())

        def place(pet: Pet, task: Task, start: int, outcome: Outcome) -> None:
            """Reserve the time and add the task to the plan with its reason."""
            free.reserve(start, task.duration_minutes)
            reason = self.explain_decision(task, outcome)
            plan.add_scheduled(ScheduledItem.starting_at(pet, task, from_minutes(start), reason))

        def skip(task: Task, outcome: Outcome) -> None:
            """Record the task as not scheduled, with its reason."""
            plan.add_unscheduled(task, self.explain_decision(task, outcome, free.remaining))

        # 1. Fixed-time tasks go exactly where the owner put them; clashes become warnings.
        fixed = [(p, t) for p, t in due if t.fixed_time is not None]
        for pet, task in sorted(fixed, key=lambda pt: (pt[1].fixed_time, pt[1].sort_key())):
            start = to_minutes(task.fixed_time)
            if not day_start <= start <= day_end - task.duration_minutes:
                skip(task, Outcome.OUTSIDE_DAY)
            elif not self.fits(task, free.remaining):
                skip(task, Outcome.NO_TIME)
            else:
                place(pet, task, start, Outcome.FIXED)

        # 2. Flexible tasks by rank: earliest gap in their window, else any gap, else skip.
        flexible = [(p, t) for p, t in due if t.fixed_time is None]
        for pet, task in sorted(flexible, key=lambda pt: pt[1].sort_key()):
            if not self.fits(task, free.remaining):
                skip(task, Outcome.NO_TIME)
            elif (start := free.find(task.duration_minutes, task.preferred_window)) is not None:
                place(pet, task, start, Outcome.SCHEDULED)
            elif task.preferred_window and (start := free.find(task.duration_minutes)) is not None:
                place(pet, task, start, Outcome.OUTSIDE_WINDOW)
            else:
                skip(task, Outcome.NO_SLOT)

        plan.scheduled_items.sort(key=lambda i: i.start_time)
        plan.warnings = self.detect_conflicts(plan.scheduled_items)
        return plan

    def mark_task_complete(self, task_id: str, on_date: Optional[date] = None) -> Optional[Task]:
        """Complete a task on any of the owner's pets; return its next occurrence if it recurs.

        Looks the task up by id across all pets (O(n)), then delegates to
        Pet.complete_task, which adds the next occurrence to the same pet.

        Raises:
            KeyError: If no pet has a task with this id.
        """
        for pet, task in self.owner.filter_tasks():
            if task.id == task_id:
                return pet.complete_task(task_id, on_date)
        raise KeyError(f"No task with id {task_id!r}")

    def rank_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority, then tiebreaker."""
        return sorted(tasks, key=Task.sort_key)

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks in clock order by earliest start; tasks with no time go last.

        A task's time is its fixed_time, else its preferred window's start (see
        Task.earliest_start). The sort key is a tuple, compared item by item:
          1. `earliest_start() is None`: False < True, so timed tasks come first.
          2. The time itself; time objects compare in clock order, so "7:30" correctly
             sorts before "12:15" (as strings it wouldn't).
          3. Task.sort_key() to break ties at the same time.
        Uses Python's stable sorted(): O(n log n). The input list is not changed.
        """
        return sorted(
            tasks,
            key=lambda t: (t.earliest_start() is None, t.earliest_start() or time.min, t.sort_key()),
        )

    def fits(self, task: Task, time_remaining: int) -> bool:
        """Return True if the task fits in the remaining minutes."""
        return task.duration_minutes <= time_remaining

    def check_conflicts(self, on_date: Optional[date] = None) -> list[str]:
        """Lightweight pre-check: warn about overlapping fixed-time tasks without building a plan.

        Only tasks due on `on_date` with a fixed_time are considered, since flexible
        tasks are placed into free gaps and can't collide. Cheap enough to run on every
        app rerun, e.g. right after a task is added.

        Args:
            on_date: The day to check; defaults to today.

        Returns:
            Warning strings (empty if none). Never raises for a conflict.
        """
        proposed = [
            ScheduledItem.starting_at(pet, task, task.fixed_time, "fixed time")
            for pet, task in self.owner.filter_tasks(due_on=on_date or date.today())
            if task.fixed_time is not None
        ]
        return self._overlap_warnings(proposed)

    def _overlap_warnings(self, items: list[ScheduledItem]) -> list[str]:
        """Return a warning for each pair of items whose times overlap; never raises.

        Checks every pair with itertools.combinations and ScheduledItem.overlaps, which
        compares full durations (start < other end and other start < end), so partial
        overlaps count and back-to-back items (one ends as the next starts) don't.
        Same pet -> "<Pet> is double-booked"; different pets -> "You're double-booked".

        O(n^2) pairs: instant for a day's worth of pet tasks, and much easier to verify
        than a sweep-line algorithm.
        """
        warnings = []
        for a, b in combinations(sorted(items, key=lambda i: i.start_time), 2):
            if not a.overlaps(b):
                continue
            if a.pet is b.pet:
                warnings.append(
                    f"{a.pet.name} is double-booked: '{a.task.title}' ({a.span()}) "
                    f"and '{b.task.title}' ({b.span()})"
                )
            else:
                warnings.append(
                    f"You're double-booked: '{a.task.title}' for {a.pet.name} ({a.span()}) "
                    f"overlaps '{b.task.title}' for {b.pet.name} ({b.span()})"
                )
        return warnings

    def detect_conflicts(self, items: list[ScheduledItem]) -> list[str]:
        """Return warnings for overlaps, preferred-window violations, and likely duplicates.

        Three checks on the finished plan:
          - overlaps: via _overlap_warnings.
          - window: an item with a preferred window that starts before it opens or ends
            after it closes (happens when the window was full).
          - duplicates: the same pet with the same title, ignoring case and spaces,
            tracked in a set in one pass.

        Returns:
            Warning strings, in that order. Never raises.
        """
        conflicts = self._overlap_warnings(items)
        ordered = sorted(items, key=lambda i: i.start_time)

        for item in ordered:
            window = item.task.preferred_window
            if window is None:
                continue
            win_start, win_end = WINDOWS[window]
            if item.start_time < win_start or item.end_time > win_end:
                conflicts.append(
                    f"'{item.task.title}' at {item.span()} is outside its preferred {window} "
                    f"window ({win_start:%H:%M}-{win_end:%H:%M})"
                )

        seen = set()
        for item in ordered:
            key = (id(item.pet), item.task.title.strip().lower())
            if key in seen:
                conflicts.append(
                    f"Possible duplicate: '{item.task.title}' is scheduled more than once for {item.pet.name}"
                )
            seen.add(key)

        return conflicts

    def explain_decision(self, task: Task, outcome: Outcome, remaining: int = 0) -> str:
        """Build the reason string for a scheduling decision from the outcome's template.

        Fills the Outcome's template with every placeholder any template might use;
        str.format ignores the ones a template doesn't mention.

        Args:
            task: The task the decision is about.
            outcome: Which decision was made; its value is the template.
            remaining: Budget minutes left, used by NO_TIME ("N short").
        """
        return outcome.value.format(
            base=f"{task.priority.value} priority" + (f" {task.category}" if task.category else ""),
            window=task.preferred_window,
            window_note=f", in its {task.preferred_window} window" if task.preferred_window else "",
            fixed=f"{task.fixed_time:%H:%M}" if task.fixed_time else "",
            minutes=task.duration_minutes,
            remaining=remaining,
            short=task.duration_minutes - remaining,
            day=f"{self.owner.day_start:%H:%M}-{self.owner.day_end:%H:%M}",
        )
