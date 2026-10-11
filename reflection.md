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
    No.
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
