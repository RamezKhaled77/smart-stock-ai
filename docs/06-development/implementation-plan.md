# Implementation Plan

## 1. Purpose

This document defines the recommended implementation sequence for SmartStock AI.

The goal is to build the application incrementally, keeping each stage small, testable, and connected to the project's requirements.

The implementation should follow the approved architecture and product documentation.

This plan is a proposed execution roadmap. It does not override existing requirements, business rules, or open decisions.

---

## 2. Implementation Principles

### 2.1 Incremental Development

Build the application in small, working increments.

Each stage should:
- Have a clear objective.
- Depend only on completed or available components.
- Produce a testable result.
- Avoid introducing unnecessary complexity.
- Be documented when it changes project behavior or decisions.

### 2.2 Architecture First

Follow the architecture defined in:

- `docs/02-architecture/tech-stack.md`
- `docs/02-architecture/system-architecture.md`
- `docs/02-architecture/project-structure.md`
- `docs/02-architecture/database-schema.md`
- `docs/02-architecture/coding-standards.md`

Do not place business logic directly inside Streamlit pages.

### 2.3 Data and ML Separation

Keep these responsibilities separate:

- Data loading and preprocessing.
- Feature engineering.
- Model training.
- Model evaluation.
- Model inference.
- Inventory business logic.
- Restocking recommendations.

The forecasting model predicts demand. It does not directly modify inventory.

### 2.4 Test Before Expanding

Do not continue building on top of broken functionality.

Run the relevant tests after each meaningful implementation stage.

### 2.5 Avoid Premature Complexity

Do not introduce:
- Unnecessary design patterns.
- Complex abstractions.
- Distributed services.
- Heavy ML frameworks.
- Unneeded authentication or authorization systems.
- Features outside the approved project scope.

---

## 3. Implementation Phases

### Phase 0: Documentation Review and Project Setup

**Objective:** Prepare the project environment and establish a clear implementation baseline.

Tasks:

1. Review all existing project documentation.
2. Identify conflicts and unresolved decisions.
3. Confirm the final project structure.
4. Initialize the Git repository if it is not already initialized.
5. Create the Python virtual environment.
6. Install the required dependencies.
7. Configure `.gitignore`.
8. Create the initial application entry point.
9. Verify that Streamlit can run.

Expected result:

- A working development environment.
- A clear project structure.
- A minimal Streamlit application.

Exit conditions:

- Dependencies install successfully.
- The application starts without errors.
- The project structure matches the architecture documentation.

---

### Phase 1: Dataset Exploration

**Objective:** Understand the selected dataset before designing the forecasting pipeline.

Tasks:

1. Obtain the dataset from its official source.
2. Inspect available files and columns.
3. Inspect data types and missing values.
4. Check duplicate records.
5. Examine date coverage.
6. Examine sales distributions.
7. Check store and item coverage.
8. Identify unusual values and possible data-quality issues.
9. Document findings.

Important:

The Kaggle Store Item Demand Forecasting dataset is a proposed dataset, not an unconditional requirement.

Before implementation, verify that the selected dataset is suitable for the intended project.

Do not invent dataset characteristics or assume that the downloaded files match the expected structure.

Expected result:

- A documented understanding of the selected dataset.
- Identified data-quality issues.
- A confirmed mapping between dataset entities and application entities, where applicable.

Exit conditions:

- The dataset structure is understood.
- Important limitations are documented.
- Any blocking data questions are resolved or explicitly recorded.

---

### Phase 2: Data Preparation Pipeline

**Objective:** Build reusable data preparation functions.

Tasks:

1. Implement dataset loading.
2. Implement column validation.
3. Implement data type conversion.
4. Implement date parsing.
5. Handle missing and invalid values according to documented rules.
6. Validate sales values.
7. Handle duplicate records according to the approved policy.
8. Prepare clean data for feature engineering.

Expected result:

A reusable preprocessing pipeline that converts raw historical data into a consistent format.

Exit conditions:

- Valid input data is processed correctly.
- Invalid input is handled safely.
- Preprocessing tests pass.
- No undocumented assumptions are introduced.

---

### Phase 3: Database and Persistence Layer

**Objective:** Implement persistent storage for operational application data.

Tasks:

1. Review the logical database schema.
2. Resolve schema decisions required for the first implementation.
3. Create the SQLite database initialization process.
4. Implement database connection management.
5. Implement required tables.
6. Implement repositories for database operations.
7. Add basic database tests.

Potential entities include:

- Products.
- Sales records.
- Inventory records.
- Inventory adjustments or transactions, if approved.
- Import history, if required.

The final schema must follow the confirmed database design.

Do not create additional tables merely because they may be useful in a future version.

Expected result:

A working SQLite persistence layer.

Exit conditions:

- The database initializes successfully.
- Required tables exist.
- Repository operations work correctly.
- Database tests pass.

---

### Phase 4: Domain and Application Services

**Objective:** Implement reusable application logic independently of the UI.

Tasks:

1. Implement product-related services.
2. Implement inventory-related services.
3. Implement sales-related services.
4. Implement input validation.
5. Implement relevant business rules.
6. Implement error handling.
7. Add unit tests.

Business logic must follow:

`docs/01-product/business-rules.md`

Important:

If a business rule remains unresolved, do not silently select an implementation.

Record the question and avoid implementing the affected behavior until the required decision is available.

Expected result:

A reusable service layer that can be called by Streamlit pages.

Exit conditions:

- Core services work independently of Streamlit.
- Business rules are covered by tests.
- Validation and error handling are implemented.

---

### Phase 5: Product and Inventory Management

**Objective:** Implement the first operational application workflow.

Tasks:

1. Build the Products and Inventory page.
2. Display available products.
3. Implement product creation.
4. Implement product updates.
5. Implement product deletion or deactivation according to the approved policy.
6. Display current stock.
7. Implement inventory adjustments according to the approved rules.
8. Display low-stock indicators where supported.

Expected result:

Users can manage products and view their inventory.

Exit conditions:

- Product operations persist correctly.
- Inventory values are validated.
- Relevant business rules are enforced.
- UI and service tests pass.

---

### Phase 6: Sales Management

**Objective:** Implement sales recording and historical sales access.

Tasks:

1. Build the Sales Management page.
2. Implement manual sales entry.
3. Validate product references.
4. Validate sales quantities and dates.
5. Apply the approved stock update policy.
6. Display sales history.
7. Add filters where required.
8. Add tests for sales and inventory interactions.

Important:

Do not assume how insufficient stock, returns, or historical imports affect inventory.

These behaviors must follow the approved business rules.

Expected result:

Users can record and review sales.

Exit conditions:

- Sales are stored correctly.
- Approved inventory updates are applied.
- Invalid sales are rejected safely.
- Sales history is accessible.

---

### Phase 7: CSV Import

**Objective:** Allow users to import historical sales data.

Tasks:

1. Build the CSV Import page.
2. Validate uploaded file format.
3. Validate required columns.
4. Validate data types.
5. Validate dates and quantities.
6. Preview imported records.
7. Report invalid rows.
8. Implement duplicate handling according to the approved policy.
9. Persist accepted records.
10. Record import results where required.

Important:

Historical sales imports must not automatically modify current stock unless an explicit stock-reconciliation workflow has been approved.

Expected result:

A reliable CSV import workflow.

Exit conditions:

- Valid CSV files can be imported.
- Invalid files produce understandable errors.
- Duplicate behavior is predictable.
- Historical imports do not unexpectedly modify inventory.

---

### Phase 8: Exploratory Data Analysis and Baseline Forecasting

**Objective:** Establish a reliable forecasting baseline before introducing more complex models.

Tasks:

1. Analyze historical sales patterns.
2. Examine trends and seasonality.
3. Check product-level data availability.
4. Implement a naive forecasting baseline.
5. Implement a historical-average baseline if appropriate.
6. Evaluate baseline predictions using chronological validation.
7. Document baseline results.

Expected result:

A measurable baseline against which ML candidates can be compared.

Exit conditions:

- Baseline predictions are generated correctly.
- Evaluation uses time-aware data splitting.
- Results and limitations are documented.

---

### Phase 9: Feature Engineering

**Objective:** Prepare features for supervised demand forecasting.

Potential features:

- Day of week.
- Month.
- Day of month.
- Lag 1.
- Lag 7.
- Rolling mean 7.
- Rolling mean 30.

Tasks:

1. Implement date-based features.
2. Implement lag features.
3. Implement rolling features.
4. Ensure rolling features do not include the current target.
5. Handle insufficient historical data.
6. Verify chronological feature generation.
7. Add feature-engineering tests.

Important:

Rolling features must use historical observations only.

For example, rolling averages should be calculated after shifting the target series appropriately.

Expected result:

A reusable feature-engineering pipeline.

Exit conditions:

- Feature values are correct.
- No target leakage exists.
- Edge cases are tested.

---

### Phase 10: Model Training and Evaluation

**Objective:** Train and evaluate candidate forecasting models.

Candidate models:

- Linear Regression.
- RandomForestRegressor.

These are candidates, not guaranteed final choices.

Tasks:

1. Prepare training data.
2. Split data chronologically.
3. Train candidate models.
4. Generate validation predictions.
5. Calculate MAE.
6. Calculate RMSE.
7. Compare candidates against baseline results.
8. Inspect prediction errors.
9. Select a model only when supported by evaluation results.
10. Save the selected model and required metadata.

Expected result:

An evaluated forecasting model.

Exit conditions:

- Training is reproducible.
- Evaluation is based on valid chronological splits.
- The selected model has documented evidence.
- Model artifacts can be loaded successfully.

If no candidate performs better than the baseline, document the result instead of forcing a model selection.

---

### Phase 11: Forecast Inference

**Objective:** Generate future demand forecasts using the selected model.

Tasks:

1. Load the saved model.
2. Validate prediction inputs.
3. Prepare required historical features.
4. Generate future predictions.
5. Support the approved forecast horizon.
6. Handle missing or insufficient history.
7. Validate prediction outputs.
8. Return structured forecast results.
9. Add inference tests.

Important:

If recursive multi-step forecasting is used, implement and test it explicitly.

Do not assume that multi-step predictions can be generated by simply passing future dates to a model trained on lag features.

Expected result:

A reusable forecasting service.

Exit conditions:

- Forecasts can be generated for supported products.
- Invalid inputs are handled safely.
- Predictions do not modify operational data.
- Inference tests pass.

---

### Phase 12: Restocking Recommendation Logic

**Objective:** Convert demand forecasts and inventory information into actionable recommendations.

Potential business formulas:

`Reorder Point = Average Daily Demand * Lead Time + Safety Stock`

`Recommended Order Quantity = max(0, Target Stock - Inventory Position)`

These formulas are proposals until the related business rules are confirmed.

Tasks:

1. Review approved inventory parameters.
2. Define required recommendation inputs.
3. Implement inventory position calculation.
4. Implement reorder-point calculation.
5. Implement recommended order quantity.
6. Handle missing inventory parameters.
7. Explain recommendation reasons.
8. Add unit tests.

Important:

The recommendation engine must remain separate from the ML forecasting model.

Recommendations are advisory only.

No automatic purchasing or inventory modification should occur.

Expected result:

A recommendation service that combines forecasts and inventory information.

Exit conditions:

- Recommendations follow approved formulas.
- Missing inputs are handled clearly.
- Recommendations do not modify inventory.
- Business logic tests pass.

---

### Phase 13: Analytics and Dashboard

**Objective:** Build the main user-facing monitoring and analytics experience.

Tasks:

1. Implement dashboard metrics.
2. Implement recent sales display.
3. Implement sales trend visualization.
4. Implement low-stock alerts.
5. Implement restocking overview.
6. Build the Sales Analytics page.
7. Add relevant filters.
8. Add actual-versus-predicted visualization if supported.
9. Add product performance analysis if included in the approved scope.

Expected result:

A useful dashboard and analytics experience based on real application data.

Exit conditions:

- Displayed metrics match their source data.
- Charts use correct aggregation logic.
- Empty and error states are handled.
- UI tests or manual verification are completed.

---

### Phase 14: Application Integration

**Objective:** Connect all implemented modules into a coherent application.

Tasks:

1. Connect Streamlit pages to application services.
2. Verify navigation.
3. Verify database persistence.
4. Verify CSV import integration.
5. Verify forecasting integration.
6. Verify restocking recommendation integration.
7. Verify error handling across pages.
8. Verify application behavior using realistic sample data.

Expected result:

An integrated SmartStock AI application.

Exit conditions:

- Core user flows work from beginning to end.
- No major integration errors remain.
- Core acceptance criteria are satisfied or documented as blocked.

---

### Phase 15: Final Testing and Quality Review

**Objective:** Verify the application before considering the core version complete.

Tasks:

1. Run all automated tests.
2. Perform manual UI testing.
3. Test invalid inputs.
4. Test empty database behavior.
5. Test CSV import edge cases.
6. Test forecasting edge cases.
7. Test inventory calculations.
8. Review error messages.
9. Review performance on the target device.
10. Review documentation consistency.
11. Record known limitations.

Expected result:

A tested and documented application.

Exit conditions:

- Core tests pass.
- Important user flows are verified.
- Remaining issues are documented.
- No feature is marked Verified without supporting evidence.

---

## 4. Recommended Development Order

The recommended high-level dependency order is:

1. Documentation and setup.
2. Dataset exploration.
3. Data preparation.
4. Database and persistence.
5. Domain and application services.
6. Product and inventory management.
7. Sales management.
8. CSV import.
9. Baseline forecasting.
10. Feature engineering.
11. Model training and evaluation.
12. Forecast inference.
13. Restocking recommendations.
14. Dashboard and analytics.
15. Integration and final testing.

Some independent tasks may be performed separately, but dependencies must be respected.

Do not start dependent implementation work before its required inputs and decisions are available.

---

## 5. Vertical Slice Strategy

Prefer completing small end-to-end workflows over creating many incomplete modules.

Example:

**Product Creation Vertical Slice**

1. Define the required product fields.
2. Implement validation.
3. Implement repository operations.
4. Implement the application service.
5. Connect the Streamlit form.
6. Persist the product.
7. Display the updated product.
8. Test the workflow.

This approach should be repeated for other important workflows.

---

## 6. AI Agent Execution Policy

The project uses:

**Autonomous with Guardrails**

The AI Agent is expected to:

- Read relevant documentation before implementation.
- Follow the existing project structure.
- Execute clearly defined tasks independently.
- Implement related tests.
- Run relevant checks after changes.
- Fix issues introduced by its own implementation.
- Update project progress.
- Update documentation when behavior or decisions change.
- Report completed work with evidence.

The AI Agent must not:

- Change approved project scope without permission.
- Silently resolve important open decisions.
- Invent requirements or dataset properties.
- Claim tests passed without running them.
- Mark unverified functionality as complete.
- Delete important data or perform destructive operations without approval.
- Add major dependencies without a clear reason.
- Introduce unnecessary architecture or complexity.

If a decision blocks implementation:

1. Identify the affected task.
2. Explain the missing decision.
3. Record the question in the appropriate documentation.
4. Continue with independent work when possible.
5. Do not implement the blocked behavior based on an unsupported assumption.

---

## 7. Definition of Done

A task is considered complete only when:

- The requested functionality is implemented.
- It follows the project architecture.
- Relevant validation exists.
- Relevant error handling exists.
- Relevant tests are written.
- Relevant tests have been executed.
- No known critical issue remains.
- Documentation is updated when necessary.
- Completion evidence is recorded.

Implementation alone does not mean verification.

Use the project progress statuses to distinguish implementation from verification.