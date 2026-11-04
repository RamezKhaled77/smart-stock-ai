# Agent Workflow

## 1. Purpose

This document defines the standard workflow that an AI coding agent must follow while working on the SmartStock AI project.

It explains how the agent should:

- Understand project context before making changes.
- Select and analyze implementation tasks.
- Plan and execute development work.
- Run appropriate tests and verify results.
- Review its own changes.
- Keep project documentation and progress records updated.
- Report completed work, blockers, and remaining tasks.

The goal is to make AI-assisted development consistent, traceable, safe, and aligned with the approved project requirements.

This document defines the detailed development workflow.

General project instructions, coding behavior, and repository-wide agent rules will be maintained separately in the root `AGENTS.md` file.

---

## 2. Agent Operating Mode

### 2.1 Selected Mode

**Autonomous with Guardrails**

The agent is expected to work independently when the requirements, dependencies, and expected outcomes are sufficiently clear.

It does not need to request permission for every routine development action.

However, it must respect project decisions, scope boundaries, data safety, and approval requirements.

### 2.2 Expected Behavior

The agent should:

- Read relevant project documentation before implementing a task.
- Understand existing code before modifying it.
- Prefer completing clearly defined tasks independently.
- Follow established architecture and coding standards.
- Write maintainable and testable code.
- Run relevant tests after implementation.
- Review its changes before reporting completion.
- Update task status and progress documentation when appropriate.
- Record important technical decisions when necessary.
- Report limitations and unresolved issues honestly.

### 2.3 Independence Boundaries

The agent may independently:

- Create and modify source code files.
- Create tests and test fixtures.
- Install dependencies that are already approved by the project setup.
- Refactor code when necessary to complete a task safely.
- Fix bugs discovered during implementation.
- Improve error handling and validation.
- Run local development commands and tests.
- Update documentation to reflect verified implementation changes.
- Perform non-destructive local development operations.

The agent must not independently:

- Change the approved project scope.
- Replace an accepted technology or architecture decision.
- Introduce major features that are not part of the agreed scope.
- Resolve important business-rule questions through unsupported assumptions.
- Perform destructive operations.
- Publish private project data.
- Deploy the application to a public environment.
- Push code or publish releases unless explicitly authorized.

---

## 3. Documentation-First Workflow

Before implementing a feature or making a significant code change, the agent must identify the relevant documentation.

### 3.1 Documentation Priority

The agent should consult documents in the following order when relevant:

1. `AGENTS.md`
2. Project overview and requirements.
3. Product feature specifications.
4. User flows and business rules.
5. Acceptance criteria.
6. System architecture and project structure.
7. Database schema and coding standards.
8. Dataset and data preprocessing documentation.
9. Machine learning documentation, when working on ML functionality.
10. Interface documentation, when working on UI functionality.
11. Implementation plan and task breakdown.
12. Decisions and known limitations.

This is a relevance-based reading order, not a requirement to read every document for every task.

### 3.2 Documentation as the Source of Truth

The agent must distinguish between:

- **Accepted:** An approved project decision or requirement.
- **Proposed:** A suggested approach that has not been formally approved.
- **Open Question:** A decision that still requires clarification.
- **Implemented:** A feature or behavior that has been added to the codebase.
- **Verified:** An implementation that has passed the required verification.

A proposed approach must not automatically be treated as an accepted requirement.

An implemented feature must not automatically be described as verified.

If multiple documents appear to conflict, the agent must not silently choose whichever interpretation is easiest.

It should:

1. Identify the conflicting statements.
2. Check the project decision log.
3. Determine whether an accepted decision already resolves the conflict.
4. If the conflict remains unresolved and materially affects implementation, stop the affected work and report the issue.

---

## 4. Standard Development Workflow

Every implementation task should follow these stages.

### Stage 1: Session Initialization

At the beginning of a development session, the agent should:

1. Read `AGENTS.md`.
2. Inspect the current project structure.
3. Check the current implementation state.
4. Review `docs/07-project-management/progress.md`.
5. Review relevant entries in `docs/07-project-management/decisions.md`.
6. Identify unfinished tasks and existing blockers.
7. Check whether previous work left incomplete or uncommitted changes.

The agent must not assume that the codebase matches the documentation perfectly.

The actual repository state must be inspected.

#### Existing Changes

If the working tree contains existing changes:

- Identify which files are already modified.
- Avoid overwriting unrelated changes.
- Do not discard user modifications.
- Do not reset the working tree to make implementation easier.
- If ownership of a change is unclear, preserve it and report the uncertainty.

### Stage 2: Task Selection

The agent should use:

- `docs/06-development/implementation-plan.md`
- `docs/06-development/task-breakdown.md`
- `docs/07-project-management/progress.md`

to identify the next suitable task.

#### Task Selection Rules

A task is suitable for implementation when:

- Its requirements are sufficiently clear.
- Its dependencies are completed or available.
- Its scope is consistent with project documentation.
- No unresolved decision prevents safe implementation.

The agent should generally prioritize:

1. Tasks required by the current implementation phase.
2. Tasks that unblock other tasks.
3. High-priority tasks.
4. Independent tasks that can be completed safely.
5. Lower-priority improvements.

The agent should not skip dependencies simply because another task appears easier.

#### Task Status

The task breakdown uses the following statuses:

- `Not Started`
- `In Progress`
- `Blocked`
- `Completed`
- `Verified`

The agent must use these statuses consistently.

A task should not be marked `Completed` simply because some code has been written.

A task should not be marked `Verified` until the required verification has actually been performed.

### Stage 3: Pre-Implementation Analysis

Before modifying code, the agent must understand the task.

It should identify:

- Task ID.
- Task objective.
- Relevant requirements.
- Related acceptance criteria.
- Dependencies.
- Expected input and output.
- Relevant modules and files.
- Required business rules.
- Required tests.
- Possible side effects.
- Relevant open questions.

The agent should inspect existing code before deciding how to implement the change.

It should prefer extending existing modules and patterns instead of creating duplicate implementations.

#### Open Questions

If a task depends on an unresolved business or technical decision:

- Search the decision log and related documentation first.
- Determine whether a safe implementation can proceed without resolving the question.
- If the question affects only one part of the task, continue with independent parts when possible.
- If the question makes the implementation ambiguous or unsafe, stop the affected part.
- Report the exact question and explain why it matters.

The agent must not invent a final business rule to avoid asking for clarification.

### Stage 4: Implementation Planning

Before significant implementation work, the agent should prepare a short internal plan.

The plan should include:

1. What needs to be implemented.
2. Which files or modules are expected to change.
3. Which existing components can be reused.
4. Which tests are required.
5. Any risks or assumptions.
6. The expected completion criteria.

The plan should be proportional to the task.

A small bug fix does not require a large planning document.

A feature involving multiple application layers should have a more detailed implementation plan.

The agent does not need approval for routine plans that follow accepted requirements.

### Stage 5: Implementation

The agent should implement the task using the existing project architecture and coding standards.

#### General Rules

- Keep responsibilities separated.
- Avoid unnecessary abstractions.
- Avoid duplicated business logic.
- Use clear function and variable names.
- Add validation at appropriate boundaries.
- Handle expected errors explicitly.
- Keep database operations separate from presentation logic.
- Prefer small, focused functions.
- Use type hints where appropriate.
- Add tests for important behavior.
- Preserve existing functionality unless a change is explicitly required.

#### Architecture Rules

The agent must respect the documented separation between:

- Streamlit presentation layer.
- Application and service layer.
- Domain and business logic.
- Repository and database layer.
- Machine learning pipeline.

Business rules should not be implemented directly inside Streamlit page code.

Database queries should not be scattered throughout unrelated application modules.

Machine learning inference should not directly modify inventory records.

Forecasting logic and inventory recommendation logic must remain separate responsibilities.

#### Implementation Scope

The agent should implement only what is necessary for the selected task and its direct dependencies.

It should avoid:

- Unrequested features.
- Large unrelated refactors.
- Premature optimization.
- Unnecessary dependencies.
- Unnecessary configuration complexity.
- Changes that make the project harder to understand.

If a small refactor is necessary to complete the task safely, it may be performed.

If the required refactor becomes a separate architectural change, the agent should report it before expanding the task.

### Stage 6: Testing and Verification

After implementation, the agent must perform the relevant verification.

The testing strategy is defined in:

`docs/06-development/testing-strategy.md`

#### Expected Verification

Depending on the task, verification may include:

- Unit tests.
- Integration tests.
- Database tests.
- Data preprocessing tests.
- Machine learning tests.
- CSV import tests.
- Application-level tests.
- Manual Streamlit UI checks.
- Regression tests.

The agent should run the most relevant tests first, followed by broader tests when practical.

#### Verification Rules

The agent must:

- Run tests that are relevant to the changed functionality.
- Inspect test failures rather than ignoring them.
- Fix failures caused by its own changes.
- Report unrelated pre-existing failures separately.
- Avoid changing tests merely to make incorrect implementation pass.
- Avoid weakening validation without a documented reason.
- Never claim that a test passed if it was not executed successfully.

If a test cannot run because of missing dependencies, unavailable data, environment limitations, or another blocker, the agent must report that limitation.

#### ML-Specific Verification

For machine learning functionality, verification should consider:

- Data leakage.
- Correct chronological splitting.
- Feature generation correctness.
- Correct target alignment.
- Model input compatibility.
- Prediction output validity.
- Evaluation metric correctness.
- Reproducibility where applicable.

A model training script running successfully does not prove that the model is useful.

Model quality must be evaluated using the documented evaluation strategy.

#### Manual UI Verification

When a task changes the Streamlit interface, the agent should verify relevant interactions where the environment allows.

Examples:

- Page navigation.
- Form validation.
- Empty states.
- Error states.
- Data display.
- User actions.
- Integration with application services.

If manual browser or visual verification is unavailable, the agent must state that it was not performed.

### Stage 7: Self-Review

Before considering a task complete, the agent must review its changes.

The review should cover:

#### Functional Correctness

- Does the implementation satisfy the task?
- Does it match the documented requirements?
- Are the expected edge cases handled?
- Does it preserve existing behavior?

#### Code Quality

- Is the code readable?
- Are responsibilities separated?
- Is business logic duplicated?
- Are error messages useful?
- Are functions unnecessarily complex?
- Are names clear and consistent?

#### Data and Security

- Are SQL queries parameterized?
- Is input validation applied?
- Are secrets excluded from source code?
- Are private datasets and local artifacts protected?
- Are destructive database operations avoided?
- Are sensitive values excluded from logs?

#### Project Consistency

- Does the implementation follow the architecture?
- Does it follow accepted decisions?
- Does it conflict with other documented requirements?
- Are related tests present?
- Are documentation updates required?

The agent should inspect the final diff and ensure that no unrelated changes were introduced.

### Stage 8: Documentation and Progress Updates

After implementation and verification, the agent must update relevant documentation.

Documentation must describe the actual state of the project, not an intended future state.

#### Task Breakdown

Update the relevant task status in:

`docs/06-development/task-breakdown.md`

Use the following guidance:

- `Not Started`: Work has not begun.
- `In Progress`: Implementation is underway.
- `Blocked`: A blocker prevents progress.
- `Completed`: The implementation is complete, but required verification may still be pending.
- `Verified`: Implementation and required verification have passed.

Include relevant evidence or notes when useful.

#### Progress

Update:

`docs/07-project-management/progress.md`

The update should reflect:

- Completed tasks.
- Verified tasks.
- Current implementation phase.
- Current blockers.
- Important remaining work.

Do not claim that an entire phase is complete if only some of its tasks are finished.

#### Decisions

Update:

`docs/07-project-management/decisions.md`

only when a meaningful project decision has been formally approved or when an existing decision needs correction.

The agent must not convert an open question into an accepted decision simply because it implemented one possible solution.

#### Known Limitations

Update:

`docs/07-project-management/known-limitations.md`

when implementation reveals a real limitation that affects the project.

Do not add speculative limitations without evidence.

#### Changelog

Update:

`docs/07-project-management/changelog.md`

when a meaningful change has actually been implemented.

The changelog should summarize user-visible features, important technical changes, bug fixes, and relevant documentation changes.

Do not record planned or incomplete functionality as released functionality.

### Stage 9: Final Report

At the end of a task or development session, the agent must provide a concise and clear report.

The report should include:

1. Task ID and objective.
2. What was implemented.
3. Important files changed.
4. Tests executed.
5. Test results.
6. Documentation updated.
7. Remaining limitations.
8. Blockers or decisions requiring user input.
9. Current task status.

The report must distinguish between:

- Implemented.
- Tested.
- Verified.
- Not tested.
- Blocked.

The agent must never exaggerate completion or verification.

---

## 5. Working with Multiple Tasks

The agent may work on multiple tasks in one session when doing so is safe and practical.

### 5.1 Independent Tasks

Independent tasks may be completed in the same session without requiring additional approval.

Examples:

- Adding validation to an existing form.
- Writing unit tests for an existing service.
- Fixing an unrelated documented bug.
- Updating documentation to match verified implementation.

### 5.2 Dependent Tasks

Tasks with dependencies must follow the implementation order defined in the task breakdown.

The agent must not implement dependent functionality on top of an unstable or incomplete prerequisite unless the task explicitly allows it.

### 5.3 Blocked Tasks

When a task is blocked:

1. Mark it as `Blocked`.
2. Document the blocker.
3. Identify what information or action is required.
4. Avoid implementing unsupported assumptions.
5. Continue with other independent tasks when possible.

A blocker affecting one task should not automatically stop the entire development session.

---

## 6. Handling Decisions and Assumptions

The agent must distinguish between technical implementation details and project-level decisions.

### 6.1 Routine Technical Decisions

The agent may independently choose implementation details when they:

- Follow the accepted architecture.
- Do not change the project scope.
- Do not introduce meaningful new dependencies or risks.
- Are reversible.
- Do not affect unresolved business rules.

Examples include:

- Choosing a clear function name.
- Extracting a small helper function.
- Selecting an appropriate test case structure.
- Reusing an existing validation pattern.

### 6.2 Decisions Requiring Approval

The agent must request approval before making decisions that:

- Change the project's approved scope.
- Replace an accepted technology.
- Change an accepted architecture decision.
- Introduce a major new dependency or service.
- Change important inventory or sales business rules.
- Change the meaning of historical data.
- Introduce automatic purchasing or external transactions.
- Require significant database migration or data deletion.
- Expose the application or its data publicly.

### 6.3 Assumption Management

When an assumption is necessary for a reversible implementation detail:

- Keep it minimal.
- Make it explicit.
- Avoid presenting it as an approved requirement.
- Document it when it affects future implementation.

When an assumption could change business behavior or data correctness, the agent must not proceed without clarification.

---

## 7. Safety and Approval Requirements

### 7.1 Destructive Operations

The agent must request explicit approval before performing operations that may permanently delete, overwrite, or damage important project data.

Examples include:

- Deleting production or user data.
- Dropping database tables.
- Resetting a database containing important data.
- Overwriting important existing files.
- Removing large parts of the project.
- Running destructive migration commands.
- Performing destructive Git operations.

The agent must not assume that a local development environment contains disposable data.

### 7.2 Git Operations

The agent may inspect Git status, diffs, history, and branches.

It may create local changes as part of normal implementation.

However:

- Do not discard unrelated working-tree changes.
- Do not reset or clean the working tree without approval.
- Do not force-push.
- Do not rewrite shared Git history.
- Do not delete branches without approval.
- Do not create commits unless explicitly requested or authorized.
- Do not push changes to remote repositories unless explicitly requested or authorized.

The final report should mention relevant Git state when it affects delivery.

### 7.3 Dependencies

The agent should prefer existing dependencies.

Before introducing a new dependency, it should consider:

- Whether the dependency is necessary.
- Whether an existing library can solve the problem.
- Compatibility with the project's Python environment.
- Maintenance and security implications.
- Installation complexity.

Minor dependencies already approved by the project setup may be installed as part of normal development.

Major dependencies, external services, or paid services require approval.

### 7.4 Deployment and External Services

Deployment is not part of routine autonomous implementation.

The agent must not:

- Deploy the application publicly without approval.
- Publish datasets or database files.
- Upload private model artifacts without authorization.
- Expose API keys or secrets.
- Connect paid services that may generate charges.
- Change external production resources.

Deployment configuration may be prepared according to the deployment documentation.

Actual deployment requires explicit user approval.

### 7.5 Sensitive Data Protection

The agent must protect:

- Credentials.
- API keys.
- Environment variables.
- Private user data.
- Local databases.
- Non-public datasets.
- Unpublished model artifacts.

It must not intentionally include sensitive values in source code, documentation, screenshots, logs, or public repositories.

---

## 8. Working with the Machine Learning Pipeline

Machine learning tasks require additional care because successful execution does not necessarily mean useful predictions.

The agent must follow the ML documentation before changing:

- Dataset preprocessing.
- Feature engineering.
- Training configuration.
- Model selection.
- Model evaluation.
- Prediction logic.
- Forecast persistence.

### 8.1 ML Development Rules

The agent must:

- Preserve chronological data ordering.
- Prevent target leakage.
- Use training-only information when fitting preprocessing steps.
- Keep training and prediction feature structures compatible.
- Evaluate models against documented baselines.
- Record relevant model configuration and evaluation results.
- Avoid claiming model accuracy without actual evaluation evidence.

### 8.2 Model Artifacts

The agent should treat trained models and metadata as generated artifacts.

It must not commit large datasets, private data, or generated artifacts unless the project explicitly requires it.

The intended artifact storage and versioning policy should follow the relevant project documentation.

### 8.3 Forecasting and Inventory Decisions

The agent must preserve the separation between:

1. Demand forecasting.
2. Inventory calculations.
3. Restocking recommendations.

A forecast is an estimate of future demand.

It is not an inventory transaction.

A restocking recommendation is advisory.

It must not automatically create purchases or modify inventory unless that behavior is explicitly approved.

---

## 9. Definition of Done

A task may be considered complete only when its relevant completion conditions have been satisfied.

### 9.1 General Completion Checklist

- [ ] The task objective is implemented.
- [ ] Implementation matches accepted requirements.
- [ ] Relevant business rules are respected.
- [ ] Existing functionality is preserved where required.
- [ ] Input validation is implemented where needed.
- [ ] Expected errors are handled.
- [ ] Relevant tests have been added or updated.
- [ ] Required tests have been executed.
- [ ] Test results have been reviewed.
- [ ] Code has been self-reviewed.
- [ ] No unrelated changes have been introduced.
- [ ] Relevant documentation has been updated.
- [ ] Task status reflects the actual implementation state.
- [ ] Remaining limitations are documented.
- [ ] Final report accurately describes the result.

Not every checklist item applies to every task.

The agent should use engineering judgment while respecting the task's acceptance criteria.

### 9.2 Verification Status

The following distinctions must remain clear:

**Implemented**

The required code or functionality has been added.

**Tested**

Relevant tests or checks have been executed.

**Verified**

The implementation satisfies the required acceptance criteria and the expected verification has passed.

A feature must not be described as verified merely because it runs without an immediate error.

### 9.3 Feature-Level Completion

A feature should be considered complete only when:

- Its required functionality exists.
- Its documented behavior is implemented.
- Its validation and error handling are appropriate.
- Its relevant acceptance criteria are satisfied.
- Its required tests have passed.
- Its integration with related components has been checked.

The feature should remain partially complete or in progress if important required behavior is missing.

---

## 10. Session Continuity

Development may happen across multiple sessions.

The agent must use project documentation to preserve continuity.

At the end of a session, it should ensure that:

- Completed work is reflected in the task breakdown.
- Project progress is updated.
- Important blockers are documented.
- Relevant decisions are recorded only when approved.
- Meaningful implemented changes are added to the changelog.
- Unfinished work remains clearly identifiable.

At the beginning of the next session, the agent should review these records before continuing.

The agent must not rely only on previous conversation context when the current repository and project documentation are available.

The repository documentation and actual implementation state should be used to reconstruct project status.

---

## 11. Workflow Summary

The standard workflow is:

1. Initialize the session.
2. Read relevant project documentation.
3. Inspect the current repository state.
4. Select a suitable task.
5. Analyze requirements and dependencies.
6. Identify unresolved decisions.
7. Prepare an implementation plan.
8. Implement the task.
9. Run relevant tests.
10. Review the implementation and diff.
11. Update documentation and progress.
12. Report the final result.

The agent should follow this workflow consistently while keeping the process proportional to the complexity of each task.

---

## 12. Core Principle

The agent is expected to be autonomous in execution, but not autonomous in redefining the project.

It should make progress independently when the path is clear, preserve existing decisions, verify its work, protect project data, and ask for approval only when a meaningful decision or risk requires human judgment.

The primary objective is not simply to produce code quickly.

It is to build a working, understandable, maintainable, and properly verified SmartStock AI application.