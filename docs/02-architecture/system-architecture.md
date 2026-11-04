# System Architecture

## 1. Overview

SmartStock AI follows a modular application architecture.

The system separates the user interface, application services, business logic, data access, and machine learning components.

The goal is to keep the application understandable, testable, and easy to maintain without introducing unnecessary architectural complexity.

The initial implementation will be a single application rather than a distributed system.

---

## 2. High-Level Architecture

The application consists of the following main layers:

1. Presentation Layer
2. Application Layer
3. Business Logic Layer
4. Data Access Layer
5. Machine Learning Layer

### Architecture Flow

```text
+------------------------------------------------+
|              Presentation Layer                |
|                                                |
|              Streamlit Interface               |
+-------------------------+----------------------+
                          |
                          v
+------------------------------------------------+
|               Application Layer                |
|                                                |
|       Application Services and Workflows       |
+-------------------------+----------------------+
                          |
              +-----------+-----------+
              |                       |
              v                       v
+---------------------------+  +---------------------------+
|    Business Logic Layer   |  |   Machine Learning Layer  |
|                           |  |                           |
| Inventory Calculations    |  | Data Preprocessing        |
| Restock Rules             |  | Feature Engineering       |
| Validation Rules          |  | Model Training            |
| Domain Operations         |  | Model Evaluation          |
|                           |  | Demand Prediction         |
+-------------+-------------+  +-------------+-------------+
              |                              |
              v                              v
+---------------------------+  +---------------------------+
|     Data Access Layer     |  |     Model Artifacts       |
|                           |  |                           |
| Repositories              |  | Saved Trained Models      |
| SQLite Database           |  | Model Metadata            |
+---------------------------+  +---------------------------+

```

---
## 3. Presentation Layer

Technology: Streamlit

Responsibilities:

- Display application pages.
    
- Collect user input.
    
- Display application data.
    
- Show charts and tables.
    
- Display validation messages.
    
- Call application services.
    

The presentation layer should not:

- Execute complex SQL queries directly.
    
- Implement inventory business rules.
    
- Train machine learning models directly.
    
- Contain duplicated calculations.
    
- Make important business decisions independently.
    

Streamlit pages should remain relatively lightweight.

## 4. Application Layer

The application layer coordinates user actions and system operations.

It connects the presentation layer with the business logic, data access, and machine learning components.

Potential services include:

- Product Service.
    
- Inventory Service.
    
- Sales Service.
    
- CSV Import Service.
    
- Analytics Service.
    
- Forecast Service.
    
- Restock Recommendation Service.
    

Responsibilities:

- Coordinate application workflows.
    
- Validate incoming operations.
    
- Retrieve required information.
    
- Call business logic functions.
    
- Save changes through repositories.
    
- Return results to the presentation layer.
    

Services should coordinate operations rather than contain every calculation themselves.

## 5. Business Logic Layer

This layer contains rules that define how the inventory system behaves.

Examples:

### Inventory Logic

- Calculate inventory position.
    
- Validate stock adjustments.
    
- Determine whether stock is below a threshold.
    
- Calculate available inventory.
    

### Restocking Logic

- Calculate reorder points.
    
- Calculate safety stock when the required inputs are available.
    
- Calculate recommended order quantities.
    
- Generate restocking recommendations.
    

### Important Separation

Demand forecasting and restocking calculations are different responsibilities.

The machine learning component predicts future demand.

The business logic component uses that prediction together with inventory information to calculate recommendations.

A prediction must not directly modify inventory quantities.

## 6. Data Access Layer

Technology: SQLite

The data access layer handles communication with the operational database.

It should provide reusable operations for:

- Creating records.
    
- Reading records.
    
- Updating records.
    
- Deleting records when permitted.
    
- Retrieving historical sales.
    
- Retrieving inventory information.
    

Repositories should isolate database queries from application services.

Business logic should not depend on SQL query details.

Database operations must use parameterized queries.

## 7. Machine Learning Layer

The machine learning layer handles demand forecasting.

It should remain independent of Streamlit pages.

### Main Components

#### 7.1 Data Preprocessing

Responsibilities:

- Validate historical sales data.
    
- Handle missing or invalid values.
    
- Normalize data formats when needed.
    
- Prepare data for feature engineering.
    

#### 7.2 Feature Engineering

Responsibilities:

- Extract date-based features.
    
- Generate lag features.
    
- Calculate rolling statistics.
    
- Prepare model input features.
    

Potential features include:

- Day of week.
    
- Month.
    
- Day of month.
    
- Lag 1.
    
- Lag 7.
    
- Rolling mean 7.
    
- Rolling mean 30.
    

The final feature set is subject to evaluation.

#### 7.3 Model Training

Responsibilities:

- Prepare training data.
    
- Train candidate models.
    
- Save trained model artifacts.
    
- Record model configuration and evaluation information.
    

Training should not happen automatically on every page interaction.

#### 7.4 Model Evaluation

Responsibilities:

- Evaluate candidate models.
    
- Calculate MAE.
    
- Calculate RMSE.
    
- Compare models against baseline approaches.
    
- Support time-based validation.
    

#### 7.5 Prediction

Responsibilities:

- Load the selected trained model.
    
- Prepare prediction input.
    
- Generate future demand predictions.
    
- Return structured prediction results.
    

Prediction should not directly update product inventory.

## 8. Forecasting and Restocking Workflow

The following workflow describes how the system generates a restocking recommendation.

1. The user selects a product and forecast period.
    
2. The Forecast Service retrieves the required historical sales data.
    
3. The ML preprocessing component prepares the data.
    
4. The feature engineering component creates model inputs.
    
5. The trained model generates demand predictions.
    
6. The Forecast Service returns the prediction results.
    
7. The Restock Recommendation Service retrieves current inventory information.
    
8. Business logic calculates the reorder point and recommended quantity using the available inputs.
    
9. The application displays the forecast and recommendation.
    

The forecasting component is read-only with respect to inventory.

The recommendation is advisory and does not automatically create a purchase order or change stock.

## 9. Historical Dataset vs Operational Database

The project distinguishes between two types of data.

### Historical Training Dataset

Used for:

- Model development.
    
- Feature engineering.
    
- Model training.
    
- Model evaluation.
    
- Historical sales analysis.
    

The dataset may be stored as CSV files.

### Operational Database

Used for:

- Product records.
    
- Current inventory.
    
- User-entered sales.
    
- Operational inventory records.
    
- Application settings or metadata when required.
    

The historical training dataset does not need to be copied entirely into SQLite.

If the Kaggle dataset is used, its `store` and `item` columns must be mapped to the application's product model.

The initial application is not assumed to support multiple branches or stores.

## 10. Model Artifacts

Trained models should be stored separately from application source code.

Joblib may be used to serialize trained models.

The application should be able to:

- Check whether a model artifact exists.
    
- Load the selected model.
    
- Handle missing or incompatible model artifacts.
    
- Display a useful error if a prediction cannot be generated.
    

Model metadata should identify the model version and relevant training information.

Loading serialized model files must be restricted to trusted artifacts.

## 11. Error Handling

Errors should be handled at the appropriate layer.

Examples:

|Error|Expected Handling|
|---|---|
|Invalid user input|Display validation message|
|Invalid CSV file|Reject import and explain the issue|
|Database failure|Log technical details and show a safe message|
|Missing model|Explain that training is required|
|Invalid prediction input|Return a clear validation error|
|Insufficient historical data|Explain why forecasting is unavailable|

The application should not silently ignore important failures.

## 12. Architectural Constraints

The initial architecture must remain:

- Modular.
    
- Lightweight.
    
- Easy to understand.
    
- Suitable for a single-user application.
    
- Compatible with local execution.
    
- Testable without launching the full Streamlit interface.
    

Avoid:

- Microservices.
    
- Unnecessary API layers.
    
- Complex dependency injection frameworks.
    
- Multiple databases without a clear requirement.
    
- Duplicated business logic.
    

## 13. Open Decisions

- Final repository implementation approach.
    
- Whether inventory movement history is required.
    
- Exact model artifact versioning strategy.
    
- Whether forecasting results should be stored in SQLite.
    
- Final application configuration strategy.
    

## 14. Related Documentation

- [Technology Stack](https://tech-stack.md?utm_source=chatgpt.com)
    
- [Project Structure](https://project-structure.md?utm_source=chatgpt.com)
    
- [Database Schema](https://database-schema.md?utm_source=chatgpt.com)
    
- Forecasting Strategy
    
- Business Rules

