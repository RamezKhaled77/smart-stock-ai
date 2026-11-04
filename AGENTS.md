# AGENTS.md

# SmartStock AI — Agent Instructions

This file defines the general rules and working instructions for any AI coding agent contributing to SmartStock AI.

These instructions are tool-independent and should work with different AI coding agents.

The agent must follow these instructions together with the relevant project documentation.

---

## 1. Project Context

SmartStock AI is a Smart Inventory and Demand Forecasting System.

The application aims to help small businesses:

- Manage products and inventory.
- Record and analyze sales.
- Forecast future product demand.
- Monitor stock levels.
- Identify potential stock shortages.
- Make better restocking decisions.

The planned application uses Python and a lightweight web interface.

Machine learning is used to forecast demand. Business rules use those forecasts, together with inventory information, to generate restocking recommendations.

The project is currently in the documentation and planning phase unless the project status indicates otherwise.

---

## 2. Documentation First

Before starting any task, the agent MUST:

1. Read this file.
2. Read `README.md`.
3. Read the documentation related to the requested task.
4. Check `docs/07-project-management/progress.md`.
5. Check `docs/07-project-management/decisions.md`.
6. Review the existing codebase before modifying it, if implementation has started.

Do not rely only on previous conversation context or assumptions.

The repository documentation is the primary reference for project requirements and accepted decisions.

### Documentation Authority

Use the following priority when information conflicts:

1. Explicitly accepted decisions in `decisions.md`.
2. Current approved requirements and specifications.
3. Current architecture and technical documentation.
4. Current implementation, when investigating existing behavior.
5. Proposed ideas and historical notes.

If a conflict cannot be resolved safely, document it and request clarification.

Never silently choose between conflicting requirements.

---

## 3. Autonomous with Guardrails

The project follows an **Autonomous with Guardrails** workflow.

The agent is expected to complete well-defined tasks and development phases independently without asking for approval after every small step.

However, the agent must respect project boundaries and request approval for important decisions.

### 3.1 Actions the Agent Can Perform Independently

The agent MAY:

- Analyze the codebase.
- Read and understand project documentation.
- Create and modify files within the approved project scope.
- Implement approved features.
- Refactor code without changing intended behavior.
- Fix bugs.
- Add appropriate tests.
- Run tests and quality checks.
- Improve error handling.
- Improve code readability and maintainability.
- Install or use already-approved dependencies.
- Update documentation when implementation details change.
- Update project progress and task status.
- Make small implementation decisions that do not change the approved architecture or product behavior.

The agent should use reasonable engineering judgment instead of asking unnecessary questions.

### 3.2 Actions Requiring User Approval

The agent MUST request approval before:

- Changing the core project purpose.
- Expanding the approved product scope significantly.
- Removing an approved core feature.
- Changing the primary technology stack.
- Replacing the database or changing its fundamental design.
- Introducing major architectural changes.
- Changing important business rules.
- Selecting a substantially different ML approach when it affects project goals.
- Adding paid services or external services that require user accounts or credentials.
- Performing destructive operations on important project data.
- Deleting important files or user data.
- Publishing, deploying, or exposing the application publicly.
- Performing actions that may expose secrets or private information.

The agent may investigate and propose alternatives independently, but must not implement approval-required changes before receiving approval.

### 3.3 When Information Is Missing

If a task depends on missing information:

1. Identify what is missing.
2. Determine whether it is a minor implementation detail or a significant decision.
3. If it is minor, choose a reasonable default and document it when relevant.
4. If it affects product behavior, architecture, data integrity, or model validity, stop the affected work.
5. Record the issue as an Open Question.
6. Explain the available options and recommend one when possible.

Do not invent business requirements, data properties, or experimental results.

### 3.4 Partial Progress

If only part of a task is blocked:

- Continue with independent work that does not depend on the unresolved decision.
- Clearly identify completed and blocked parts.
- Do not create temporary assumptions that could become misleading implementation decisions.

---

## 4. Task Execution Workflow

For every substantial task, follow this workflow.

### Step 1: Understand

- Read the task description.
- Identify the relevant documentation.
- Inspect the current implementation.
- Understand dependencies and existing behavior.
- Identify acceptance criteria.

### Step 2: Plan

Create a practical implementation plan.

The plan should identify:

- Files to create or modify.
- Main implementation steps.
- Dependencies.
- Potential risks.
- Required tests.
- Documentation updates.

For small tasks, a short internal plan is sufficient.

For substantial tasks, present the plan before implementation when the task requires user alignment or includes significant uncertainty.

### Step 3: Implement

- Follow the approved architecture.
- Keep changes focused.
- Prefer simple and maintainable solutions.
- Reuse existing components and utilities where appropriate.
- Avoid unnecessary abstractions.
- Do not introduce unrelated changes.

### Step 4: Verify

Run the relevant checks.

Depending on the task, these may include:

- Unit tests.
- Integration tests.
- Data validation.
- ML evaluation.
- Application startup checks.
- Static analysis.
- Formatting and linting.

Never claim that a test passed unless it was actually executed successfully.

If a check cannot be performed, clearly state why.

### Step 5: Review

Review the changes for:

- Correctness.
- Consistency with requirements.
- Data integrity.
- Security issues.
- Error handling.
- Performance concerns.
- Unintended behavior changes.
- Unnecessary complexity.

### Step 6: Update Documentation

Update the relevant documentation whenever implementation changes affect:

- Requirements.
- Features.
- Business rules.
- Architecture.
- Database schema.
- Data processing.
- ML methodology.
- Setup instructions.
- Testing instructions.

Update project progress and decisions when necessary.

### Step 7: Report

Provide a clear summary containing:

1. What was completed.
2. Important implementation details.
3. Files created or modified.
4. Tests and checks performed.
5. Known issues or limitations.
6. Decisions requiring user approval.
7. Suggested next task.

---

## 5. Engineering Principles

Follow these principles throughout development.

### Simplicity

- Prefer simple solutions over unnecessary complexity.
- Do not introduce a framework or library without a clear reason.
- Avoid building infrastructure that the project does not need.

### Maintainability

- Use clear and descriptive names.
- Keep functions focused.
- Separate responsibilities.
- Avoid duplicated business logic.
- Use consistent project conventions.

### Readability

- Write code that a Python beginner with basic programming knowledge can understand.
- Prefer explicit logic over unnecessarily clever implementations.
- Add comments when they explain why something is done, not merely what the code does.

### Reliability

- Validate external input.
- Handle expected errors.
- Protect important data from accidental modification.
- Avoid silent failures.
- Use deterministic and reproducible processes where practical.

### Learning and Explainability

This is an educational project.

The agent should:

- Prefer understandable implementations.
- Explain important technical decisions.
- Explain the role of major libraries.
- Avoid hiding all logic behind complex abstractions.
- Include useful explanations in completion reports.
- Avoid unnecessary advanced techniques that make the project difficult to understand.

---

## 6. Python Guidelines

When implementing Python code:

- Follow consistent Python naming conventions.
- Use descriptive variable and function names.
- Keep functions reasonably small.
- Use type hints where they improve clarity.
- Use docstrings for important public functions and modules.
- Handle exceptions intentionally.
- Avoid unnecessary global state.
- Keep configuration separate from business logic.
- Do not hardcode secrets or private credentials.
- Use virtual environments for dependency isolation.
- Keep dependencies documented.

Use the project's approved coding standards once finalized:

`docs/02-architecture/coding-standards.md`

---

## 7. Data and Database Rules

Data must be handled carefully.

The agent MUST:

- Validate imported CSV files.
- Check required columns and data types.
- Handle missing and invalid values explicitly.
- Avoid silently changing original data.
- Separate raw data from processed data when appropriate.
- Preserve data consistency.
- Use parameterized SQL queries.
- Avoid destructive database operations without approval.
- Document database schema changes.
- Keep data processing reproducible.

Never assume that a dataset contains information that has not been verified.

The dataset documentation is located in:

`docs/03-data/`

---

## 8. Machine Learning Rules

Machine learning functionality must be evidence-based.

The agent MUST:

- Understand the target variable before training.
- Inspect the dataset before feature engineering.
- Use appropriate time-aware validation for forecasting.
- Prevent data leakage.
- Establish a baseline before evaluating complex models.
- Compare candidate models using consistent evaluation methods.
- Report actual evaluation results.
- Avoid claiming that a model is accurate without supporting measurements.
- Keep training and prediction responsibilities clear.
- Document the features used by the model.
- Keep model artifacts reproducible where practical.

The agent MUST NOT:

- Select a model only because it is popular.
- Randomly split chronological forecasting data without justification.
- Use future information to predict the past.
- Invent model metrics.
- Confuse predicted demand with inventory quantities.
- Treat a model prediction as a guaranteed business outcome.

The ML documentation is located in:

`docs/04-machine-learning/`

---

## 9. Product and Business Logic Rules

Keep business logic separate from UI code and ML prediction code.

For example:

- The forecasting component predicts demand.
- The inventory component manages stock quantities.
- The recommendation component applies inventory rules to produce restocking suggestions.
- The UI displays information and collects user input.

Do not mix all these responsibilities into a single large page or function.

All approved business rules must be documented in:

`docs/01-product/business-rules.md`

---

## 10. Dependencies and External Services

Before introducing a new dependency:

1. Check whether an existing library already solves the problem.
2. Confirm that the dependency is compatible with the project.
3. Evaluate its complexity and maintenance status.
4. Explain why it is needed when the choice is significant.
5. Update the dependency documentation or requirements file.

Do not introduce paid services, external APIs, or services requiring credentials without approval.

Prefer free and locally runnable solutions when they satisfy project requirements.

---

## 11. Testing Requirements

Testing is part of implementation, not an optional final step.

The agent should add tests for important logic, especially:

- Inventory calculations.
- Sales calculations.
- Data validation.
- Forecasting feature generation.
- Prediction output handling.
- Restocking recommendations.

Tests should cover normal cases, edge cases, and invalid input.

Do not modify or remove tests simply to make an implementation pass.

Follow:

`docs/06-development/testing-strategy.md`

---

## 12. Documentation Maintenance

Documentation must remain consistent with the actual project.

Whenever an important change is made:

- Update the relevant specification.
- Update architecture documentation when architecture changes.
- Update database documentation when the schema changes.
- Update ML documentation when the forecasting approach changes.
- Update `decisions.md` when a decision is accepted, rejected, or replaced.
- Update `progress.md` when meaningful tasks are completed.
- Update `changelog.md` when notable project changes occur.

Do not duplicate the same detailed information across multiple files.

Use links to reference the original documentation instead.

---

## 13. Security and Privacy

The agent MUST:

- Never expose secrets or credentials.
- Never commit `.env` files containing real secrets.
- Avoid logging sensitive information.
- Validate user-provided input.
- Avoid unsafe SQL construction.
- Avoid destructive operations without approval.
- Never upload project data to external services without authorization.

If a security issue is discovered, explain its impact and recommended fix.

---

## 14. Definition of Done

A task is considered complete only when:

- The requested behavior is implemented.
- The implementation follows approved requirements.
- Relevant tests have been added or updated.
- Relevant checks have been executed.
- No known critical issue remains unresolved.
- Documentation has been updated when necessary.
- The final report accurately describes the result.

If some requirements remain incomplete, the task must be reported as partially completed rather than complete.

---

## 15. Communication Style

When reporting work:

- Be clear and direct.
- Explain important technical decisions in understandable language.
- Avoid unnecessary technical jargon.
- Distinguish facts from assumptions.
- Report failures honestly.
- Mention important trade-offs.
- Do not claim that something works without verification.

Because this is an educational project, include short explanations of important implementation choices so the project owner can understand the work.

---

## 16. Final Rule

The goal is not simply to produce working code.

The goal is to build a practical, understandable, maintainable, and well-documented Smart Inventory and Demand Forecasting System.

Follow the approved project scope, use evidence for important technical decisions, work independently within the defined guardrails, and ask for approval only when it is genuinely necessary.