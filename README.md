# SmartStock AI

**Smart Inventory & Demand Forecasting System**

SmartStock AI is a web-based inventory management and demand forecasting system designed to help small businesses manage their products, monitor stock levels, analyze historical sales, forecast future demand, and make better restocking decisions.

The project combines traditional inventory management with machine learning to support data-driven business decisions.

> Project status: v1 core complete — all 16 phases implemented, 435 automated tests passing; owner's manual UI walk-through pending (checklist ready).

---

## 1. Project Overview

Small businesses often manage their inventory using spreadsheets, manual records, or basic inventory tools.

These methods can make it difficult to:
- Predict how much stock will be needed.
- Avoid running out of popular products.
- Prevent overstocking and unnecessary storage costs.
- Understand sales trends.
- Decide when and how much to reorder.

SmartStock AI aims to address these problems through a simple inventory management application supported by demand forecasting.

The system allows users to manage products and sales, analyze historical data, receive demand predictions, and view restocking recommendations.

## 2. Main Objectives

The main objectives are to:

1. Build a practical inventory management application.
2. Store and manage product and sales information.
3. Analyze historical sales data.
4. Apply machine learning to forecast product demand.
5. Provide useful inventory insights and restocking recommendations.
6. Present information through a clear and interactive dashboard.
7. Demonstrate how AI and Python libraries can solve a real business problem.

## 3. Target Users

The initial target users are:

- Small retail businesses.
- Small shop owners.
- Businesses that manage products and daily sales.
- People who need a simple way to understand inventory and sales.

The initial version will focus on a single business with a manageable product catalog.

Multi-branch management and advanced enterprise features are outside the initial scope.

## 4. Main Features

The planned core features include:

- Dashboard with inventory and sales summaries.
- Product management.
- Inventory quantity management.
- Sales recording and management.
- CSV data import.
- Historical sales analysis.
- Machine learning-based demand forecasting.
- Low-stock alerts.
- Restocking recommendations.

Feature details and priorities are documented in:

`docs/01-product/features.md`

## 5. Planned Technology Stack

The following technologies are currently proposed:

| Area | Proposed Technology |
|---|---|
| Programming Language | Python |
| Web Application | Streamlit |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| Data Visualization | Plotly |
| Database | SQLite |
| Model Persistence | Joblib |
| Testing | Pytest |

These are proposed choices, not all formally accepted decisions.

See `docs/02-architecture/tech-stack.md` for details and decision status.

## 6. Machine Learning Approach

The project will investigate time-series demand forecasting using historical sales data.

The initial approach is to:

1. Collect and inspect historical sales data.
2. Clean and prepare the data.
3. Create time-based and historical sales features.
4. Train and compare suitable regression models.
5. Evaluate models using appropriate forecasting metrics.
6. Generate demand predictions.
7. Use predictions as inputs for inventory recommendations.

Potential models include:

- A simple baseline model.
- Linear Regression.
- Random Forest Regressor.

The final model was selected on measured evaluation results, not assumptions (DEC-027/DEC-057; see `docs/04-machine-learning/model-evaluation.md`).

See `docs/04-machine-learning/` for the complete ML documentation.

## 7. Project Documentation

The `docs/` directory contains the project's specifications and development guidelines.

| Directory | Purpose |
|---|---|
| `00-foundation/` | Project definition, goals, requirements, terminology |
| `01-product/` | Features, user flows, business rules, acceptance criteria |
| `02-architecture/` | Technology choices, system design, database, coding standards |
| `03-data/` | Dataset, data dictionary, preprocessing, validation |
| `04-machine-learning/` | Forecasting strategy, features, training, evaluation |
| `05-interface/` | UI specifications and dashboard design |
| `06-development/` | Roadmap, tasks, agent workflow, setup, testing, deployment |
| `07-project-management/` | Decisions, progress, limitations, changelog |

## 8. AI Agent Instructions

The project supports AI-assisted development using different coding agents.

Before making changes, an AI Agent must:

1. Read the root `AGENTS.md`.
2. Read the relevant documentation for the requested task.
3. Check the current project status and accepted decisions.
4. Understand the task and its acceptance criteria.
5. Follow the Autonomous with Guardrails workflow.

The agent must not assume that every proposed technology, model, dataset, or feature has been approved.

See:
- `AGENTS.md`
- `docs/06-development/agent-workflow.md`
- `docs/07-project-management/decisions.md`

## 9. Current Project Status

Version 1 is implemented: the Streamlit application has seven pages
(Dashboard, Products & Inventory, Restocking Recommendations, Sales
Management, Sales Analytics, Demand Forecast, Data Import) backed by a
layered service architecture, and the demand-forecasting model
(Random Forest, DEC-057) is trained, artifact-persisted, and integrated
behind the product ↔ dataset-item mapping (DEC-060).

Current priorities:

- Owner walk-through of the manual test checklist
  (`docs/06-development/manual-test-plan.md`).
- Optional advanced features (TASK-049 export reports; further v2 ideas).

The current status and completed work are tracked in:

`docs/07-project-management/progress.md`

## 10. Important Project Principles

- Keep the application simple and practical.
- Prefer understandable and maintainable code.
- Use existing Python AI and ML libraries where appropriate.
- Avoid unnecessary complexity and heavy technologies.
- Validate assumptions using data and experiments.
- Prevent data leakage in forecasting.
- Separate machine learning predictions from business decision logic.
- Test important calculations and application behavior.
- Keep documentation synchronized with implementation.
- Do not add features outside the approved project scope without recording and reviewing the change.

## 11. Getting Started

Full setup instructions live in `docs/06-development/setup-guide.md`
(virtual environment, dependencies, dataset, database). The short
version, from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py     # app.py adds src/ to sys.path itself
PYTHONPATH=src .venv/bin/python -m pytest    # full automated suite (430 tests)
```

For background reading, start with:

1. `AGENTS.md`
2. `docs/00-foundation/project-overview.md`
3. `docs/00-foundation/goals-and-scope.md`
4. `docs/01-product/features.md`
5. `docs/06-development/agent-workflow.md`

---

## Project Status

**Phase:** v1 implemented — verification and documentation finishing

**Implementation:** Seven pages, services/domain/ML layers, trained model integrated (see `docs/07-project-management/progress.md`)

**Documentation:** Kept synchronized with implementation (TASK-048)

**Development Workflow:** Autonomous with Guardrails