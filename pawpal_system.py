"""PawPal+ core system: owners, pets, tasks, and the daily scheduler.

Skeleton generated from diagrams/uml.mmd. Methods are stubs; logic comes next.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum
from typing import Optional


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    id: str
    title: str
    duration_minutes: int
    priority: Priority
    category: Optional[str] = None          # feeding, exercise, meds, grooming
    preferred_window: Optional[str] = None  # e.g. "morning"
    recurrence: Optional[str] = None        # none, daily, weekly
    completed: bool = False

    def validate(self) -> None:
        """Raise ValueError if duration <= 0 or priority is invalid."""
        pass

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        pass

    def update(self, **changes) -> None:
        """Apply field changes to this task, then re-validate."""
        pass

    def sort_key(self) -> tuple:
        """Return a key that orders by priority first, then a tiebreaker."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: Optional[int] = None
    special_needs: Optional[str] = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet."""
        pass

    def edit_task(self, task_id: str, **changes) -> None:
        """Update the task with the given id."""
        pass

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id."""
        pass

    def get_tasks(self, include_completed: bool = True) -> list[Task]:
        """Return this pet's tasks, optionally excluding completed ones."""
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    day_start: time = time(8, 0)
    day_end: time = time(20, 0)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, pet_name: str) -> None:
        """Remove the pet with the given name."""
        pass

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Return the pet with the given name, or None."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return tasks across all of this owner's pets."""
        pass

    def set_constraints(self, available_minutes: int, day_start: time, day_end: time) -> None:
        """Update the owner's daily time budget and working hours."""
        pass


@dataclass
class ScheduledItem:
    task: Task
    pet: Pet
    start_time: time
    end_time: time
    reason: str

    def duration(self) -> int:
        """Return the length of this item in minutes."""
        pass

    def overlaps(self, other: ScheduledItem) -> bool:
        """Return True if this item's time range overlaps another's."""
        pass


@dataclass
class Plan:
    date: date
    scheduled_items: list[ScheduledItem] = field(default_factory=list)
    unscheduled_items: list[tuple[Task, str]] = field(default_factory=list)

    def total_time_used(self) -> int:
        """Return total scheduled minutes."""
        pass

    def time_remaining(self, available_minutes: int) -> int:
        """Return minutes left in the budget after scheduled items."""
        pass

    def add_scheduled(self, item: ScheduledItem) -> None:
        """Add an item to the schedule."""
        pass

    def add_unscheduled(self, task: Task, reason: str) -> None:
        """Record a task that could not be scheduled, with the reason."""
        pass

    def summary(self) -> str:
        """Return a readable explanation of the day's plan."""
        pass


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate_plan(self) -> Plan:
        """Build and return today's Plan from the owner's pets and tasks."""
        pass

    def rank_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority, then tiebreaker."""
        pass

    def fits(self, task: Task, time_remaining: int) -> bool:
        """Return True if the task fits in the remaining minutes."""
        pass

    def detect_conflicts(self, items: list[ScheduledItem]) -> list[str]:
        """Return descriptions of overlaps or preferred-window violations."""
        pass

    def explain_decision(self, task: Task, outcome: str) -> str:
        """Build the reason string for a scheduling decision."""
        pass
