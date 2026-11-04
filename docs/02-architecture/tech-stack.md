# Technology Stack

## 1. Overview

SmartStock AI uses Python as its primary programming language.

The application is designed as a lightweight web-based inventory management and demand forecasting system.

The selected technologies focus on:

- Simplicity and ease of development.
- Compatibility with Python-based AI and data science libraries.
- Low hardware requirements.
- Free and open-source tools where possible.
- Maintainability and clear separation of responsibilities.

Some technologies are proposed choices and may be revised during implementation if technical evidence requires it.

---

## 2. Core Technologies

### 2.1 Python

**Status:** Proposed

Python is the main programming language used throughout the project.

Reasons:
- Strong ecosystem for data analysis and machine learning.
- Simple syntax and fast development.
- Good integration with the selected libraries.
- Suitable for the project's academic requirements.

### 2.2 Streamlit

**Status:** Proposed

Streamlit will be used to build the web application interface.

Responsibilities:
- Display application pages.
- Collect user input.
- Display tables, charts, and metrics.
- Connect UI actions to application services.

Streamlit should not contain complex business logic or machine learning implementation details.

### 2.3 Pandas

**Status:** Proposed

Pandas will handle tabular data operations.

Responsibilities:
- Load CSV datasets.
- Clean and transform sales data.
- Prepare historical data for machine learning.
- Aggregate sales by product and date.
- Support analytical operations.

### 2.4 NumPy

**Status:** Proposed

NumPy will support numerical operations and calculations used in data processing and machine learning.

### 2.5 Scikit-learn

**Status:** Proposed

Scikit-learn will provide the machine learning tools used for demand forecasting.

Potential responsibilities:
- Model training.
- Model evaluation.
- Feature preprocessing.
- Regression models.
- Prediction.

The final model selection will depend on validation results.

### 2.6 Plotly

**Status:** Proposed

Plotly will be used for interactive charts and visualizations.

Potential use cases:
- Historical sales trends.
- Demand forecasts.
- Actual versus predicted demand.
- Product performance.
- Inventory analytics.

### 2.7 SQLite

**Status:** Proposed

SQLite will serve as the application's operational database.

It will store application data such as:
- Products.
- Inventory information.
- Sales records.
- Inventory movements, if approved.
- Other operational records required by the application.

SQLite is suitable for the initial single-user academic application.

It does not require a separate database server.

### 2.8 Joblib

**Status:** Proposed

Joblib will be used to save and load trained machine learning models.

The application should reuse a saved model for predictions instead of training the model every time a user opens the forecasting page.

### 2.9 Pytest

**Status:** Proposed

Pytest will be used for automated testing.

It will support tests for:
- Business logic.
- Data preprocessing.
- Feature engineering.
- Forecasting.
- Inventory calculations.
- Application services.

---

## 3. Supporting Technologies

| Technology | Purpose | Status |
|---|---|---|
| Git | Version control | Proposed |
| GitHub | Source code hosting | Proposed |
| CSV | Historical data exchange | Proposed |
| Python venv | Environment isolation | Proposed |
| pip | Dependency installation | Proposed |

---

## 4. Development Environment

The project should run on a standard Python environment.

Recommended setup:

- Python 3.11 or a compatible version supported by the selected dependencies.
- A virtual environment.
- Git for version control.
- VS Code or another Python-compatible editor.

The project must avoid unnecessary hardware requirements.

GPU acceleration is not required for the planned machine learning models.

---

## 5. Machine Learning Approach

The project will use traditional machine learning models rather than deep learning.

Potential model candidates:

- Historical Average Baseline.
- Naive Forecast.
- Linear Regression.
- Random Forest Regressor.

These are candidates, not final approved model selections.

The final model must be selected based on evaluation results using a time-based validation strategy.

---

## 6. Technology Selection Principles

Any technology added to the project should satisfy at least one clear requirement.

Before introducing a new dependency, consider:

1. Is it necessary for a current requirement?
2. Can an existing library handle the task?
3. Does it add unnecessary complexity?
4. Is it compatible with the development environment?
5. Is it actively maintained and reasonably documented?

Avoid adding technologies simply because they are popular.

---

## 7. Explicitly Out of Scope for the Initial Version

The initial version does not require:

- React or Next.js.
- FastAPI or a separate backend server.
- Docker.
- TensorFlow or PyTorch.
- Cloud database services.
- Distributed processing systems.
- Microservices.

These technologies may be reconsidered only if future requirements justify them.

---

## 8. Open Decisions

The following decisions require validation during implementation:

| Decision | Current Position |
|---|---|
| Python version | 3.11 or compatible version |
| Main forecasting model | To be evaluated |
| Final feature set | To be evaluated |
| SQLite access approach | To be selected |
| Dependency version pinning | To be defined |
| Deployment platform | Open |

---

## 9. Related Documentation

- [System Architecture](system-architecture.md)
- [Project Structure](project-structure.md)
- [Database Schema](database-schema.md)
- [Coding Standards](coding-standards.md)
- [Forecasting Strategy](../04-machine-learning/forecasting-strategy.md)