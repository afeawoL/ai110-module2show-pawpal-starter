"""PawPal+ core system: owners, pets, tasks, and the daily scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import date, time
from enum import Enum
from typing import Optional


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Lower rank sorts first.
PRIORITY_RANK = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}

# Named preferred windows as (start, end) times.
WINDOWS = {
    "morning": (time(6, 0), time(12, 0)),
    "afternoon": (time(12, 0), time(17, 0)),
    "evening": (time(17, 0), time(22, 0)),
}

RECURRENCES = {None, "none", "daily", "weekly"}


def to_minutes(t: time) -> int:
    """Convert a time of day to minutes since midnight."""
    return t.hour * 60 + t.minute


def from_minutes(m: int) -> time:
    """Convert minutes since midnight to a time of day."""
    return time(m // 60, m % 60)


@dataclass
class Task:
    id: str
    title: str
    duration_minutes: int
    priority: Priority
    category: Optional[str] = None          # feeding, exercise, meds, grooming
    preferred_window: Optional[str] = None  # a key of WINDOWS, e.g. "morning"
    recurrence: Optional[str] = None        # none, daily, weekly
    completed: bool = False

    def __post_init__(self) -> None:
        """Convert a string priority to Priority, then validate the new task."""
        # Accept "high"/"medium"/"low" strings for convenience (e.g. from the UI).
        if isinstance(self.priority, str):
            try:
                self.priority = Priority(self.priority.lower())
            except ValueError:
                raise ValueError(f"Invalid priority: {self.priority!r}")
        self.validate()

    def validate(self) -> None:
        """Raise ValueError if the title, duration, priority, window, or recurrence is invalid."""
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
        if self.recurrence not in RECURRENCES:
            raise ValueError(f"Invalid recurrence: {self.recurrence!r}")

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def update(self, **changes) -> None:
        """Apply field changes and re-validate, rolling back if the result is invalid."""
        allowed = {f.name for f in fields(self)} - {"id"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Cannot update field(s): {sorted(unknown)}")

        if isinstance(changes.get("priority"), str):
            changes["priority"] = Priority(changes["priority"].lower())

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

    def get_all_tasks(self) -> list[Task]:
        """Return tasks across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

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

    def duration(self) -> int:
        """Return the length of this item in minutes."""
        return to_minutes(self.end_time) - to_minutes(self.start_time)

    def overlaps(self, other: ScheduledItem) -> bool:
        """Return True if this item's time range overlaps another's."""
        return self.start_time < other.end_time and other.start_time < self.end_time


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
        """Add an item to the schedule, keeping items in start-time order."""
        self.scheduled_items.append(item)
        self.scheduled_items.sort(key=lambda i: i.start_time)

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
                    f"  {item.start_time:%H:%M}-{item.end_time:%H:%M}  "
                    f"{item.task.title} ({item.pet.name}, {item.duration()} min, "
                    f"{item.task.priority.value}) - {item.reason}"
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
        """Build a Plan by placing ranked tasks back to back, skipping any that don't fit."""
        plan = Plan(date=plan_date or date.today())

        # Keep each task paired with its pet so ScheduledItem can reference it.
        pet_for = {}
        pending = []
        for pet in self.owner.pets:
            for task in pet.get_tasks(include_completed=False):
                pet_for[id(task)] = pet
                pending.append(task)

        remaining = self.owner.daily_budget()
        cursor = to_minutes(self.owner.day_start)

        for task in self.rank_tasks(pending):
            if self.fits(task, remaining):
                start, end = cursor, cursor + task.duration_minutes
                plan.add_scheduled(ScheduledItem(
                    task=task,
                    pet=pet_for[id(task)],
                    start_time=from_minutes(start),
                    end_time=from_minutes(end),
                    reason=self.explain_decision(task, "scheduled"),
                ))
                cursor = end
                remaining -= task.duration_minutes
            else:
                plan.add_unscheduled(task, self.explain_decision(task, "no_time"))

        plan.warnings = self.detect_conflicts(plan.scheduled_items)
        return plan

    def rank_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority, then tiebreaker."""
        return sorted(tasks, key=Task.sort_key)

    def fits(self, task: Task, time_remaining: int) -> bool:
        """Return True if the task fits in the remaining minutes."""
        return task.duration_minutes <= time_remaining

    def detect_conflicts(self, items: list[ScheduledItem]) -> list[str]:
        """Return descriptions of overlaps or preferred-window violations."""
        conflicts = []

        for i, a in enumerate(items):
            for b in items[i + 1:]:
                if a.overlaps(b):
                    conflicts.append(f"'{a.task.title}' overlaps '{b.task.title}'")

        for item in items:
            window = item.task.preferred_window
            if window is None:
                continue
            win_start, win_end = WINDOWS[window]
            if item.start_time < win_start or item.end_time > win_end:
                conflicts.append(
                    f"'{item.task.title}' at {item.start_time:%H:%M}-{item.end_time:%H:%M} "
                    f"is outside its preferred {window} window "
                    f"({win_start:%H:%M}-{win_end:%H:%M})"
                )

        return conflicts

    def explain_decision(self, task: Task, outcome: str) -> str:
        """Build the reason string for a scheduling decision."""
        if outcome == "scheduled":
            reason = f"{task.priority.value} priority"
            if task.category:
                reason += f" {task.category}"
            if task.preferred_window:
                reason += f", prefers {task.preferred_window}"
            return reason
        if outcome == "no_time":
            return (
                f"needs {task.duration_minutes} min but not enough time left "
                f"after higher-priority tasks"
            )
        return outcome
