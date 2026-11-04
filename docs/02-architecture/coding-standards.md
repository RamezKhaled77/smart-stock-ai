

# Coding Standards

## 1. Overview

This document defines coding standards for SmartStock AI.

The purpose is to keep the codebase readable, consistent, testable, and easy to maintain.

These standards apply to Python source code, database operations, data processing, and machine learning components.

---

## 2. General Principles

All code should follow these principles:

- Readability over unnecessary cleverness.
- Simplicity over premature abstraction.
- Clear responsibility for each module.
- Reusable business logic.
- Minimal duplication.
- Meaningful naming.
- Explicit error handling.
- Testable functions.

Do not introduce abstractions without a real requirement.

---

## 3. Python Style

Follow PEP 8 as the general Python style guide.

### Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Variables | snake_case | current_stock |
| Functions | snake_case | calculate_reorder_point |
| Classes | PascalCase | InventoryService |
| Constants | UPPER_SNAKE_CASE | DEFAULT_LEAD_TIME |
| Modules | snake_case | forecast_service.py |

Names should describe their purpose.

Avoid unclear names such as:

- `x`
- `temp`
- `data1`
- `process()`

unless they are appropriate within a small, obvious context.

---

## 4. Functions

Functions should have one clear responsibility.

Prefer small functions that are easy to understand and test.

Example:

```python
def calculate_reorder_point(
    average_daily_demand: float,
    lead_time_days: int,
    safety_stock: int,
) -> float:
    return (
        average_daily_demand * lead_time_days
        + safety_stock
    )

```

Avoid functions that combine unrelated operations such as:

- Reading CSV files.
    
- Updating database records.
    
- Training models.
    
- Rendering Streamlit components.
    

These responsibilities should be separated.

## 5. Type Hints

Use Python type hints for functions and important data structures.

Type hints should be introduced consistently, especially for:

- Function parameters.
    
- Return values.
    
- Service interfaces.
    
- Important data transformations.
    

Full strict typing is not required initially.

The goal is to improve readability and reduce avoidable mistakes.

## 6. Documentation

Use docstrings for:

- Public functions.
    
- Important classes.
    
- Non-obvious business rules.
    
- Complex data transformations.
    
- Important ML workflows.
    

Docstrings should explain purpose, important inputs, and expected output.

Avoid comments that simply repeat what the code already says.

Prefer explaining why a decision exists rather than describing every line.

## 7. Business Logic

Business rules must have a single clear implementation.

For example:

- Reorder point calculations belong in domain/business logic.
    
- Inventory validation belongs in domain/business logic.
    
- Restock recommendation calculations should not be duplicated across Streamlit pages.
    

Use pure functions when practical.

A pure function should:

- Depend only on its inputs.
    
- Avoid modifying external state.
    
- Return predictable results.
    
- Be easy to test.
    

Business logic should not depend on Streamlit.

## 8. Database Standards

Database access must be isolated from UI code.

Rules:

- Use parameterized SQL queries.
    
- Avoid building SQL statements through unsafe string concatenation.
    
- Enable SQLite foreign key enforcement.
    
- Use transactions for related database operations.
    
- Handle database errors explicitly.
    
- Keep database initialization separate from normal application workflows.
    

Do not expose database implementation details to Streamlit pages.

## 9. Data Processing Standards

Data processing code should:

- Validate expected columns.
    
- Handle missing values explicitly.
    
- Use consistent date formats.
    
- Avoid modifying original raw datasets.
    
- Document important transformations.
    
- Avoid unnecessary repeated processing.
    

Raw historical datasets should remain unchanged.

Processed data should be generated through documented preprocessing steps.

## 10. Machine Learning Standards

Machine learning code should be separated into clear stages:

1. Data validation.
    
2. Preprocessing.
    
3. Feature engineering.
    
4. Training.
    
5. Evaluation.
    
6. Prediction.
    

Important rules:

- Use chronological splitting for time-series evaluation.
    
- Avoid data leakage.
    
- Keep training separate from prediction.
    
- Save and load model artifacts consistently.
    
- Record important model configuration and evaluation metrics.
    
- Compare candidate models against a baseline.
    
- Do not claim a model is accurate without evaluation results.
    

Feature engineering must ensure that future information is not used to predict past or current targets.

## 11. Error Handling

Do not silently ignore errors.

Use appropriate exceptions and validation messages.

Examples:

- Invalid input should produce a clear validation error.
    
- Missing files should be handled explicitly.
    
- Invalid datasets should be rejected with useful explanations.
    
- Database errors should not expose sensitive technical information to the UI.
    
- Missing model artifacts should produce a clear message explaining what is required.
    

Avoid catching every exception without a clear reason.

## 12. Streamlit Standards

Streamlit pages should focus on presentation and user interaction.

Rules:

- Keep pages relatively small.
    
- Move business calculations into reusable functions.
    
- Move database access into repositories or services.
    
- Avoid repeating the same UI logic unnecessarily.
    
- Use clear labels and validation messages.
    
- Handle loading and error states.
    
- Use caching only when it is appropriate and does not cause stale operational data.
    

Streamlit session state should be used carefully and consistently.

## 13. Testing Standards

Use pytest for automated tests.

Prioritize testing:

- Inventory calculations.
    
- Reorder point calculations.
    
- Recommended order quantities.
    
- Data validation.
    
- CSV preprocessing.
    
- Feature engineering.
    
- Forecasting input preparation.
    
- Prediction output handling.
    

Tests should cover:

- Normal cases.
    
- Boundary cases.
    
- Invalid inputs.
    
- Missing data.
    
- Unexpected values.
    

Avoid relying exclusively on manual UI testing.

A feature is not considered verified simply because its code has been written.

## 14. Security and Configuration

Rules:

- Never commit passwords or API keys.
    
- Keep local database files out of version control.
    
- Validate uploaded files.
    
- Avoid unsafe file paths.
    
- Use trusted model artifacts only.
    
- Do not expose sensitive exception details to users.
    

Configuration should be centralized where practical.

## 15. Git Standards

Use meaningful commit messages.

Examples:

- `feat: add product management`
    
- `feat: implement demand forecasting`
    
- `fix: handle invalid sales quantities`
    
- `test: add inventory calculation tests`
    
- `docs: update database schema`
    

Avoid committing:

- Virtual environments.
    
- Cache directories.
    
- Temporary files.
    
- Local SQLite databases.
    
- Large generated datasets.
    
- Unnecessary model artifacts.
    

## 16. AI Agent Development Rules

Any AI coding agent working on SmartStock AI must follow the project's approved autonomy policy:

Autonomous with Guardrails

The agent may execute clear, independent development tasks without requesting approval for every routine step.

However, it must:

- Follow approved requirements and architecture.
    
- Read relevant documentation before implementation.
    
- Avoid changing project scope without approval.
    
- Never invent requirements, data, or test results.
    
- Run relevant tests after implementation.
    
- Report actual results and limitations.
    
- Update documentation and progress records when necessary.
    
- Stop and ask for clarification when ambiguity materially affects correctness.
    
- Request approval before destructive or irreversible operations.
    

The agent should explain important implementation decisions and keep the project understandable to its developer.

## 17. Related Documentation

- [Technology Stack](https://tech-stack.md?utm_source=chatgpt.com)
    
- [System Architecture](https://system-architecture.md?utm_source=chatgpt.com)
    
- [Project Structure](https://project-structure.md?utm_source=chatgpt.com)
    
- Testing Strategy
    
- Implementation Plan