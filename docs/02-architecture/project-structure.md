
# Project Structure

## 1. Overview

This document defines the proposed source code organization for SmartStock AI.

The structure separates application pages, services, business logic, data access, and machine learning components.

It should remain simple enough for a small academic project while allowing future improvements.

The structure is a proposal and may be adjusted when implementation reveals a genuine need.

---

## 2. Proposed Directory Structure

```text
smartstock-ai/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── AGENTS.md
├── .gitignore
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
│
├── database/
│   ├── schema.sql
│   └── README.md
│
├── models/
│   ├── artifacts/
│   └── README.md
│
├── src/
│   └── smartstock/
│       ├── __init__.py
│       │
│       ├── pages/
│       │   ├── dashboard.py
│       │   ├── products.py
│       │   ├── sales.py
│       │   ├── analytics.py
│       │   └── forecasting.py
│       │
│       ├── services/
│       │   ├── product_service.py
│       │   ├── inventory_service.py
│       │   ├── sales_service.py
│       │   ├── import_service.py
│       │   ├── analytics_service.py
│       │   ├── forecast_service.py
│       │   └── recommendation_service.py
│       │
│       ├── domain/
│       │   ├── inventory.py
│       │   ├── forecasting.py
│       │   ├── recommendations.py
│       │   └── validators.py
│       │
│       ├── repositories/
│       │   ├── product_repository.py
│       │   ├── sales_repository.py
│       │   └── inventory_repository.py
│       │
│       ├── ml/
│       │   ├── preprocessing.py
│       │   ├── features.py
│       │   ├── training.py
│       │   ├── evaluation.py
│       │   └── prediction.py
│       │
│       ├── database/
│       │   ├── connection.py
│       │   └── initialization.py
│       │
│       └── utils/
│           ├── dates.py
│           └── formatting.py
│
├── scripts/
│   ├── train_model.py
│   └── prepare_dataset.py
│
├── tests/
│   ├── test_inventory.py
│   ├── test_recommendations.py
│   ├── test_preprocessing.py
│   ├── test_features.py
│   └── test_prediction.py
│
└── docs/
    ├── 00-foundation/
    ├── 01-product/
    ├── 02-architecture/
    ├── 03-data/
    ├── 04-machine-learning/
    ├── 05-interface/
    ├── 06-development/
    └── 07-project-management/
```

---
## 3. Root Files

### app.py

The main Streamlit application entry point.

Responsibilities:

- Configure the Streamlit application.
    
- Display the main navigation.
    
- Initialize required application components.
    
- Load the appropriate pages.
    

It should not contain the application's main business logic.

### config.py

Contains centralized application configuration.

Examples:

- Database file path.
    
- Dataset paths.
    
- Model artifact paths.
    
- Application settings.
    

Avoid storing passwords, API keys, or other secrets in source code.

### requirements.txt

Contains the project's Python dependencies.

Dependencies should be added only when they are actually required.

## 4. Main Directories

### data/

Contains local datasets used by the project.

- `raw/`: Original datasets that should remain unchanged.
    
- `processed/`: Cleaned or transformed datasets generated during preprocessing.
    

Large datasets should not be committed to Git unless there is a clear reason.

### database/

Contains database-related assets such as the initial SQL schema.

The actual SQLite database file should normally be generated locally and excluded from Git.

### models/

Contains saved machine learning model artifacts.

The `artifacts/` directory may contain serialized models and related metadata.

Generated model artifacts should not be committed automatically.

### src/smartstock/pages/

Contains Streamlit page implementations.

Pages should focus on UI rendering and user interaction.

### src/smartstock/services/

Contains application services.

Services coordinate workflows between the UI, repositories, business logic, and ML components.

### src/smartstock/domain/

Contains core business rules and domain-level calculations.

Functions in this directory should avoid depending on Streamlit or database implementation details.

### src/smartstock/repositories/

Contains database access operations.

Each repository should focus on a specific group of operational records.

### src/smartstock/ml/

Contains machine learning implementation details.

This directory must remain independent of Streamlit UI code.

### src/smartstock/database/

Contains database connection and initialization logic.

### src/smartstock/utils/

Contains small reusable helpers that do not belong to a more specific module.

Avoid turning this directory into a place for unrelated application logic.

### scripts/

Contains scripts for tasks such as:

- Preparing historical datasets.
    
- Training machine learning models.
    
- Running standalone development operations.
    

### tests/

Contains automated tests.

Tests should focus on individual functions and services wherever possible.

## 5. Dependency Direction

The intended dependency direction is:

```shell
Pages
  |
  v
Services
  |
  +------> Domain Logic
  |
  +------> Repositories
  |
  +------> ML Components
```

Important rules:

- Domain logic must not depend on Streamlit.
    
- ML components must not depend on Streamlit.
    
- Repositories must not contain UI code.
    
- Pages should not contain raw SQL queries.
    
- Services should coordinate operations rather than duplicate domain calculations.
    
- Shared business rules should have one clear implementation.
    
---

## 6. Import Conventions

Use consistent absolute imports from the `smartstock` package.

Example:

```shell
from smartstock.domain.inventory import calculate_reorder_point
from smartstock.repositories.product_repository import ProductRepository
```

The exact execution configuration may need adjustment depending on how Streamlit is launched.

The reliable development command is `streamlit run app.py` from the repository root (app.py adds `src/` to `sys.path` itself, so no manual environment variable is needed).

## 7. Structure Evolution Rules

Do not create additional directories or modules without a clear responsibility.

A new module may be introduced when:

- A component has a distinct responsibility.
    
- Existing modules are becoming difficult to maintain.
    
- A requirement needs a reusable implementation.
    
- Tests benefit from separating the logic.
    

Avoid creating empty abstractions for hypothetical future features.

## 8. Open Decisions

- Final packaging and import configuration.
    
- Whether the domain directory needs additional modules.
    
- Whether database repositories should use classes or simple functions.
    
- Exact dataset and model artifact naming conventions.
    
- Whether generated reports need a separate directory.
    

## 9. Related Documentation

- [System Architecture](https://system-architecture.md?utm_source=chatgpt.com)
    
- [Technology Stack](https://tech-stack.md?utm_source=chatgpt.com)
    
- [Database Schema](https://database-schema.md?utm_source=chatgpt.com)
    
- [Coding Standards](https://coding-standards.md?utm_source=chatgpt.com)

