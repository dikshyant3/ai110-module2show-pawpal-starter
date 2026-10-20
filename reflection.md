# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
My initial UML design is creating a simple pet care management system where an owner could manage multiple pets and their daily activities. 


- What classes did you include, and what responsibilities did you assign to each?

I used four main classes: Owner, Pets, Tasks, and Scheduler. The Owner class manages the pets registered in the system. The Pet class consists the pet information such as name, and species and the tasks they need to perform. The Task class represents activities such as feeding, walking, medication, and appointments. Finally, the Scheduler class organizes all the tasks, sort them by time, and helps the owner manage daily activities.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
I identified a few issues in the initial design.

The first issue was that tasks did not store which pet they belonged to. Since the Owner class returns a combined list of tasks, the Scheduler would not be able to identify the correct pet. To address this, I added a pet_name attribute to the Task class and updated Pet.add_task() to assign the pet's name when adding a task.

Another issue was that multiple pets could have the same name, making it difficult to identify the correct pet. I updated the design so that Owner.add_pet() would reject duplicate pet names.

I also changed the sorting design to consider both the scheduled date and time instead of time alone. This ensures that tasks are displayed in the correct order when activities are scheduled across multiple days.

These changes helped me improve the original design before implementing the actual functionality. They also made the system better prepared for multi-pet scheduling, recurring tasks, and filtering.

The final UML is saved as [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd). It reflects the implemented class attributes and methods, the Owner-to-Pet and Pet-to-Task relationships, and the Scheduler's dependency on Owner for task retrieval and on Task objects for sorting, filtering, conflict checks, and completion.



---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

`Scheduler.detect_conflicts()` only flags tasks that are at the *exact* same date and time. It doesn't look out for overlapping time durations. For instance, a 30-minute walk at 8:00 and breakfast at 8:15 overlap, but they won't be flagged, because `Task` has no duration field.

This approach is good because most pet care tasks are scheduled at specific times (feeding a pet at 8:00 or giving medicines at 11:00). It checks whether two tasks are scheduled at the same date and time. This helps catch the scheduling mistakes and keeps the system simple. It groups tasks by `(due_date, scheduled_time)` in a single pass and shows plain warning messages instead of crashing when it finds a mistake. Checking whether the tasks overlap would be more complicated because we have to add a `duration` to every task and compare time ranges, which adds work for the user and more edge cases (for example, tasks that run past midnight) for little benefit at this stage.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

I used Claude Code in VS Code at each stage of the project. First it turned my class descriptions into a Mermaid UML diagram (diagrams/uml_draft.mmd). Then it translated that diagram into a Python skeleton in pawpal_system.py, using dataclasses for Task, Pet, and Owner. Next I asked it to review the skeleton for missing relationships and logic bottlenecks. The review found that Task had no link to its pet, so once Owner.get_all_tasks() combined every task, the Scheduler couldn't tell which pet each task belonged to. It added a pet_name field and updated the UML to match. After that, it implemented the core methods (mark_complete, add_task, add_pet, get_pet, get_all_tasks, and a basic get_schedule), wrote main.py as a demo, created two pytest tests, and updated the README with real output.

- What kinds of prompts or questions were most helpful?

The most helpful prompts were specific and set clear limits. Examples were "use the actual method signatures from my code," "do not implement Phase 4 algorithms yet," "do not modify app.py," and "explain any necessary design changes before making them." Asking for a review of "class responsibilities, UML consistency, relationships, and multi-pet scheduling support" also worked well, because it pointed the AI at real design problems instead of general advice.

In the later implementation work, codebase inspection, targeted edits, and running pytest/AppTest were the most useful assistant capabilities. They helped connect the UI to the existing Scheduler methods and verify that its conflict warnings, filters, and recurring-task completion still worked. For example, the assistant's initial suggestions for a richer task model included duration and priority fields; I kept the design focused on the fields and exact-time behavior already implemented instead of expanding the architecture.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

When I first described my four classes, the AI began writing a UML diagram based on its own assumptions. It added attributes I hadn't asked for, such as available_minutes, preferences, and priority. I rejected that change and wrote a more detailed prompt that listed the exact attributes and methods for each class. I also required that the Scheduler access tasks through Owner.get_all_tasks(), and that the design stay simple and beginner-level. Later, during Phase 2, I stopped the AI partway through and gave it a shorter, more focused version of the instructions.

I did not use a separate chat session for every phase of this latest implementation, so I cannot claim separate chats directly helped this work. I kept the requests phase-specific instead: first expanding and verifying tests, then improving the interface, then aligning the UML and documentation. When I do split work into separate chats, keeping each one focused on a phase helps by reducing unrelated context and making it easier to return to the relevant files and decisions.

- How did you evaluate or verify what the AI suggested?

I checked that the code matched my UML and that every change came with an explanation. The AI also ran the code after each step instead of just saying it worked. It checked the syntax, ran main.py to confirm that tasks from both Buddy and Luna appeared with the correct pet names, and ran the pytest tests. While testing, it found that plain `pytest` failed with a ModuleNotFoundError even though `python -m pytest` passed, and it fixed this by adding a pytest.ini file so pytest can import from the project root. It also pointed out limits instead of hiding them, such as get_schedule() not sorting tasks yet and `pytest --cov` needing the pytest-cov plugin.

---

## 4. Testing and Verification

**a. What you tested**

I expanded `tests/test_pawpal.py` to check five groups of behavior:

- **Task and ownership behavior:** completion state, task recurrence rules, automatic pet-name tagging, pet task lookup, duplicate pet rejection, and collecting an owner's tasks. These checks protect the links between model objects so tasks stay associated with the right pet.
- **Schedule algorithms:** retrieving every task or only one day's tasks, chronological sorting by date and then time, stable ordering for equal slots, and filtering by pet and completion state. These tests verify normal scheduling as well as empty and unknown-filter cases.
- **Conflict detection:** exact date-and-time collisions, multiple conflict groups, same-pet and cross-pet clashes, and non-clashes for different dates, a one-minute difference, or completed tasks. These checks pin down the scheduler's exact-time rule.
- **Recurring completion and errors:** daily and weekly next dates, a year rollover, no recurrence for a one-time task, preserving time/pet and resetting completion on the next occurrence, duplicate descriptions resolved by date or time, and errors for repeat completion, missing pets/tasks, and foreign task objects. These are important because a wrong match or recurrence could silently change the wrong task or assign work to the wrong pet.
- **Streamlit flow:** an AppTest starts the app, confirms the empty-pet state, adds a pet and a daily task, then completes it and checks that the next occurrence is displayed. This provides a basic integration check that the UI is wired to the backend methods.

I ran `python -m pytest`: **31 passed in 0.63s**. The Streamlit checks cover the empty state, adding and completing a recurring task, feedback for blank/duplicate submissions, and a conflict warning that remains visible when the current pet filter hides one of the clashing tasks. No genuine backend bug was exposed. During test development I corrected assumptions about task ownership and Streamlit's AppTest widget/path API; those were test setup issues, not application fixes.

**b. Confidence**

I rate the scheduler **4 out of 5 stars** based on the current evidence. The tests cover central sorting, filtering, conflict, recurrence, lookup, and task completion behaviors, including boundary/error cases, and the representative Streamlit workflow passes. Next, I would test interactive filter combinations and duplicate-pet/error messages through the Streamlit interface, then run it in a browser to cover behavior beyond in-process AppTest.

---

## 5. Reflection

**a. What went well**

I am most satisfied that the tests now exercise both the scheduler's backend rules and a user-facing Streamlit workflow without changing the four-class architecture. The schedule tests verify more than the happy path: they clarify tie ordering, what counts as a conflict, and recurring completion behavior. The UI test also checks that completing a daily item surfaces tomorrow's task.

**b. What you would improve**

If I had another iteration, I would add broader UI interaction tests for changing pet/status filters, duplicate-pet submission, and blank inputs. I would also consider whether task descriptions need a more explicit unique identifier in a future version; here, the scheduler handles duplicate descriptions by requiring a date and/or time, which is tested but still asks the caller to disambiguate.

**c. Key takeaway**

My key takeaway is that the AI can generate and refine code quickly, but I remain responsible for the architecture and evidence. Being the lead architect means keeping the model aligned with the real requirements, rejecting extra complexity when it is not needed, checking that the UI uses the intended backend methods, and validating claims with tests and actual program output. I also learned that tests should describe the actual model contract: adding a task to a pet deliberately sets its `pet_name`, so a valid foreign-task test must use a task from a separate owner rather than expecting a mismatched name to remain.
