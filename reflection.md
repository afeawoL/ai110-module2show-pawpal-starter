# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
  - Add an owner and a pet
  - Add and edit tasks (duration + priority)
  - Set available time for the day
  - Generate a daily plan
  - View the plan with explanations

- What classes did you include, and what responsibilities did you assign to each?
  - Owner - Stores the owner’s name and daily constraints (available time, start/end hours), holds the list of pets, and provides access to all pets’ tasks.
  - Pet - Stores pet details (name, species, optional age/needs), holds its own tasks, and handles adding, editing, and removing them.
  - Task - Stores title, duration, priority, and optional fields (time window, category, recurrence, completed flag); validates its own data and can mark itself complete.
  - Scheduler - Gathers tasks from the owner’s pets, ranks them by priority with a consistent tiebreaker, fits them into the available time, detects conflicts and overflow, records a reason for each decision, and returns a Plan.
  - Plan - Stores the scheduled items (task, pet, start/end time, reason) and the unscheduled items with reasons; reports total time used and produces a readable explanation.

**b. Design changes**

- Did your design change during implementation?
  - Yes. The five original classes survived, but each grew as real scheduling needs showed up, and I added three small helpers.
- If yes, describe at least one change and why you made it.
  - **Task got real time and date fields.** My first design only had a vague `preferred_window`, so there was nothing to sort by time and no way to say "meds at 07:30 sharp." I added `fixed_time` (accepting `"HH:MM"` strings), `due_date`, and `completed_on`. Recurring tasks then became possible: completing a daily task creates a new copy due the next day instead of flipping a `completed` flag that never resets.
  - **`Owner.get_all_tasks()` became `filter_tasks()`.** Returning a plain list of tasks lost track of which pet each task belonged to, and the scheduler needed that for every scheduled item. `filter_tasks()` returns `(pet, task)` pairs and doubles as the filtering feature (by pet, status, priority, due date).
  - **New helpers to keep `generate_plan` readable:** `FreeTime` (tracks the day's free gaps and remaining budget), `Outcome` (one enum holding every reason message), and `Plan.warnings` (so conflicts are reported instead of crashing). The UML in `diagrams/uml.mmd` was updated after each change.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
  - **Time budget:** the smaller of the owner's available minutes and the length of their day.
  - **Day hours:** nothing is scheduled before the day starts or after it ends.
  - **Priority:** high → medium → low, with shorter tasks first and then title as tiebreakers.
  - **Exact times:** tasks pinned to a time (e.g. meds at 07:30) are placed exactly there.
  - **Preferred windows:** morning, afternoon or evening. Tasks go in their window if there's room, otherwise in the first free gap with a warning.
  - **Due dates and recurrence:** only tasks due that day (or overdue) are scheduled.
- How did you decide which constraints mattered most?
  - I ranked them by what would hurt the pet most if ignored. Exact times come first because things like medication often can't move. Priority comes next because a missed feeding matters more than a missed brushing. Preferred windows come last: they're "nice to have," so the scheduler bends them (with a warning) rather than dropping a task.
  - The time budget is a hard limit because an owner can't create extra hours, but the plan always says exactly how many minutes a skipped task was short, so the owner can adjust.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  - The scheduler is **greedy and priority-first**: it sorts tasks by priority (then shorter duration, then title) and places each one in the earliest free gap that fits, never going back to rearrange earlier choices. It does not search for the combination of tasks that uses the most of the owner's time.
  - This means it can leave time unused. In my demo (`main.py`), the owner has 150 minutes. The scheduler places 135 minutes of tasks, then skips the 45-minute Bath ("needs 45 min, only 15 left (30 short)"). An optimal "knapsack" search that only tried to fill the most minutes would instead drop Laser play (20 min, medium) and Brushing (15 min, low) to fit Bath, using 145 minutes. The greedy approach never considers that swap.
  - Conflicts are handled the same lightweight way: when two fixed-time tasks overlap (checked by full duration, not just matching start times), the scheduler keeps both and adds a warning instead of moving or rejecting one.
- Why is that tradeoff reasonable for this scenario?
  - For pet care, priority matters more than filling every minute. The "better" knapsack answer above would give up a medium-priority play session for a low-priority bath, just to use 10 more minutes. Greedy-by-priority guarantees that a higher-priority task is never bumped to make room for a lower-priority one.
  - It's predictable and easy to explain. Every decision has a one-line reason ("high priority, fixed at 07:30", "5 short"), which an owner can understand at a glance. A knapsack result is harder to justify ("why was Laser play dropped?").
  - It's fast and simple to test. A day has only around 5–30 tasks, so speed was never the issue, but the greedy logic is short enough that each rule has its own test.
  - The cost is small and visible: anything skipped is listed with exactly how many minutes it was short, so the owner can raise their available time or lower a priority and regenerate.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
  - I used Claude Code at every stage: reviewing my UML before coding, generating class skeletons from it, implementing the logic, writing and strengthening tests, refactoring, connecting the Streamlit UI, and drafting documentation.
  - **Most effective features for building the scheduler:**
    - **Running code, not just writing it.** After each change it ran the test suite and `main.py`, and it drove the Streamlit app with Streamlit's test runner (adding pets, clicking buttons, reading tables). That caught real bugs I wouldn't have seen just reading code: a conflict warning showing twice, and a warning about tasks that were outside the owner's day and would never be scheduled.
    - **Review before building.** Asking it to review my design and list gaps (e.g. "`get_all_tasks()` loses which pet a task belongs to," "a `completed` flag never resets for daily tasks") shaped the design before I wrote logic.
    - **Options instead of a single answer.** Asking "how could this be simplified? pick a few choices" gave me five options with tradeoffs, so I made the decision instead of accepting whatever came first.
    - **Edits across many files at once.** One request could update `pawpal_system.py`, the tests, `main.py`, `app.py`, and the UML together, keeping them in sync.
    - **Explaining concepts in my own code's terms:** how `st.session_state` keeps objects alive between reruns, and how a `lambda` sort key handles `"HH:MM"` times.
- What kinds of prompts or questions were most helpful?
  - Review prompts ("list 3–5 core behaviors to verify," "what are the most important edge cases") were more useful than "write X," because they surfaced gaps I hadn't thought of.
  - Asking for a short list of choices and then picking specific ones ("implement all but wait to do #5").
  - Specific, scoped requests that named the file and method ("add logic to `Task` or `Scheduler` so a daily task creates the next one").

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
  - **Rejected: adding a `pytest.ini` file.** When the tests couldn't import `pawpal_system`, the AI fixed it by adding a config file. I asked it to try again without that file. It turned out `python -m pytest` works with no extra configuration, so I kept the project simpler and used that command instead.
  - **Modified: the simplification plan.** The AI proposed five cleanups. I accepted four (a simpler pairwise conflict check, the `FreeTime` helper, an `Outcome` enum, and a `ScheduledItem.starting_at()` constructor), and deferred the fifth (moving completed recurring tasks into a separate history list). That would add a new concept to the data model, and since app data resets each browser session, the list never grows large enough to matter yet. Keeping the model smaller was the cleaner choice for now.
- How did you evaluate or verify what the AI suggested?
  - I required every change to pass the full test suite and to keep `main.py`'s output the same. For the refactor, the AI saved the demo output first and compared it line by line afterwards.
  - I asked for edge-case reviews and then tests for them. A check where we deliberately planted bugs in a copy of the code showed one AI-written test was too weak: it still passed when tasks were ranked by duration instead of priority, because both test tasks had the same length. It was rewritten so priority and duration disagree. A test passing isn't proof that it tests anything.
  - I checked README and reflection claims against real output, e.g. the "Bath is 30 short" example and the CLI sample, rather than trusting numbers from earlier runs.

**c. Organizing the work**

- How did using separate chat sessions for different phases help you stay organized?
  - **[Fill in from your own experience.]** *Note from the AI: everything I can see happened in one continuous session, so I can't describe separate sessions for you. If you did use separate chats (e.g. one for UML/design, one for implementation, one for testing, one for docs), describe what that gave you: a fresh context focused on one goal, less earlier back-and-forth leaking into later decisions, easier review of each phase. If you used one session, say so honestly, and describe what you did instead to stay organized: working phase by phase (UML → skeleton → logic → tests → UI → docs), committing at milestones, and updating the UML after each design change.*

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
  - 55 tests in `tests/test_pawpal.py`, run with `python -m pytest`, covering:
    - **Sorting:** chronological order with tasks added out of order and unpadded `"7:30"`; ties at the same time broken by priority; an empty list.
    - **Priority and budget:** high beats low when time is short; shorter first within a priority; the budget is the smaller of minutes and day length; a zero budget doesn't crash.
    - **Placement:** fixed times are exact; flexible tasks use their window and fall back when it's full; a task ending exactly at day end is allowed, one minute past is skipped.
    - **Recurrence:** daily → tomorrow, weekly → +7 days, an overdue task → today + 1, Dec 31 → Jan 1, across a leap day, one-off tasks don't repeat, completing twice doesn't duplicate.
    - **Conflicts:** same pet and different pets; partial overlaps; back-to-back isn't a conflict; completed, future and outside-the-day tasks are ignored; warnings instead of crashes.
    - **Filtering and validation:** by pet and status; bad input rejected; failed edits roll back.
- Why were these tests important?
  - They lock in the rules a pet owner relies on: meds never get bumped for grooming, and a daily walk comes back tomorrow. They also made refactoring safe: I simplified the scheduler's core and knew within a second whether anything changed.

**b. Confidence**

- How confident are you that your scheduler works correctly?
  - Fairly confident (about 4 out of 5). Every core rule has a test, and planting bugs on purpose confirmed the key tests fail when the logic breaks. The demo and the app were also checked end to end. The remaining risk is in combinations I haven't tried, not in the individual rules.
- What edge cases would you test next if you had more time?
  - Many tasks competing for one small window (e.g. five "morning" tasks in a short morning).
  - Editing a task's time or recurrence after it has already been completed.
  - A task whose preferred window lies entirely outside the owner's day.
  - Very long-running use: hundreds of completed recurring copies building up (the deferred history feature).

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
  - The scheduler explains itself. Every task in the plan has a one-line reason, and every skipped task says exactly how many minutes it was short. The same logic powers the terminal demo, the Streamlit app, and the tests, so all three always agree.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
  - Move completed recurring tasks into a separate history list (the deferred cleanup), so the active task list stays short over time.
  - Save data between browser sessions; right now refreshing the page starts over.
  - Let the scheduler suggest a fix for conflicts (e.g. "move Breakfast to 07:40") instead of only warning.
  - Possibly offer an optional "fill the most time" mode for owners who care more about using every minute than about strict priority.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
  - **Being the "lead architect" means owning the decisions and the verification, not the typing.** The AI could write a scheduler, tests, a UI, and documentation faster than I could, and most of it was good. But it also produced a test that passed while checking nothing, numbers that went stale after the demo changed, and a config file the project didn't need. What kept the system clean was:
    - starting from a design (the UML) and making the AI keep it updated;
    - asking for options and tradeoffs, then choosing, including saying "not yet";
    - requiring evidence (tests, real output, the app actually running) instead of accepting "done";
    - questioning results that looked right but hadn't been proven, like a test that passed on the first try.
  - The AI is a powerful builder. My job was to decide what to build, keep it simple, and check that it really works.
