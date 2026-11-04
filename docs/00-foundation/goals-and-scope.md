# Goals and Scope

## 1. Purpose

This document defines the goals, boundaries, priorities, and exclusions of SmartStock AI.

It helps prevent unnecessary feature expansion and keeps development focused on delivering a complete and demonstrable system.

## 2. Main Project Goal

Build a practical web-based inventory management system that uses historical sales data and machine learning to forecast product demand and support inventory replenishment decisions.

The system should demonstrate how Python and existing AI libraries can be used to solve a real business problem.

## 3. Specific Goals

### 3.1 Product Goals

- Provide a centralized place to manage products.
- Track current inventory quantities.
- Record and review sales.
- Import historical sales data.
- Display useful inventory and sales summaries.
- Identify products that may require restocking.
- Present understandable recommendations.

### 3.2 Data Goals

- Work with structured historical sales data.
- Validate imported data.
- Handle missing and invalid values.
- Prepare data for forecasting.
- Maintain a clear separation between raw and processed data.

### 3.3 Machine Learning Goals

- Build a demand forecasting pipeline.
- Establish a baseline forecasting method.
- Experiment with suitable regression models.
- Evaluate forecasting performance using time-aware validation.
- Compare models using appropriate metrics.
- Generate future demand estimates.

### 3.4 Educational Goals

- Apply Python to a practical project.
- Use existing data science libraries.
- Understand the machine learning workflow.
- Demonstrate model training and evaluation.
- Explain the relationship between predictions and business decisions.
- Build an application that integrates data analysis and machine learning.

## 4. Initial Product Scope

The initial version will focus on a single business.

The core system should include the following modules.

### 4.1 Dashboard

The dashboard should summarize important information, such as:

- Total products.
- Current inventory overview.
- Products with low stock.
- Recent sales.
- Sales trends.
- Products requiring attention.

Exact metrics and calculations will be defined in the interface documentation.

### 4.2 Product Management

Users should be able to:

- Add products.
- View products.
- Edit product information.
- Update inventory quantities.
- View stock status.

### 4.3 Sales Management

Users should be able to:

- Record sales.
- View sales history.
- Import sales records from CSV files.
- Validate imported data.

### 4.4 Demand Forecasting

The system should:

- Use historical sales data.
- Prepare forecasting features.
- Train and evaluate suitable models.
- Generate demand predictions.
- Display prediction results.

### 4.5 Restocking Recommendations

The system should:

- Compare current stock with expected demand.
- Consider approved inventory parameters.
- Identify potential stock shortages.
- Recommend restocking quantities.
- Explain the reasoning behind recommendations.

## 5. Feature Priorities

Features are divided into three priority levels.

### 5.1 Core Features

These features define the minimum useful application.

| Feature | Priority |
|---|---|
| Product Management | Core |
| Inventory Tracking | Core |
| Sales Recording | Core |
| CSV Sales Import | Core |
| Basic Dashboard | Core |
| Demand Forecasting | Core |
| Low-Stock Alerts | Core |
| Restocking Recommendations | Core |

### 5.2 Advanced Features

These may be implemented after the core system works reliably.

| Feature | Priority |
|---|---|
| Advanced Sales Analytics | Advanced |
| Actual vs. Predicted Charts | Advanced |
| Product Performance Analysis | Advanced |
| Exportable Reports | Advanced |
| More Forecasting Models | Advanced |

### 5.3 Future Possibilities

These features are not part of the initial implementation commitment.

| Feature | Status |
|---|---|
| Supplier Management | Future |
| Multiple Branches | Future |
| Automated Purchase Orders | Future |
| External POS Integration | Future |
| AI Chat Assistant | Future |
| Advanced Role Management | Future |
| Mobile Application | Future |

Future features require explicit scope approval before implementation.

## 6. Out of Scope

The initial version will NOT attempt to provide:

- Full ERP functionality.
- Accounting and financial management.
- Payment processing.
- E-commerce storefront functionality.
- Supplier marketplace functionality.
- Automated supplier communication.
- Complex warehouse management.
- Multi-company management.
- Enterprise-level access control.
- Real-time integrations with external POS systems.
- Deep learning infrastructure.
- Large-scale cloud deployment.

These exclusions help keep the project achievable.

## 7. Initial Business Assumptions

The following assumptions are proposed and require validation.

### Business Assumptions

- The initial system manages one business.
- Products have identifiable names or codes.
- Sales records include a product identifier, date, and quantity.
- Users can provide or import historical sales records.
- Inventory quantities are maintained by the application.
- Restocking recommendations are advisory.

### Data Assumptions

- Historical sales data is available.
- The forecasting dataset can be mapped to the application's product structure.
- Product-level demand can be estimated from historical records.
- The available historical data is sufficient for meaningful experiments.

These assumptions must be reviewed during data investigation.

## 8. Initial User Model

The initial version assumes one primary user role:

**Business Owner / Inventory Manager**

This user can:

- Manage products.
- Record sales.
- Import data.
- Review inventory.
- View forecasts.
- Review restocking recommendations.

Authentication and multiple user roles are not yet confirmed requirements.

## 9. Project Constraints

### Time

The project is an academic deliverable and should remain achievable within the available development period.

### Hardware

The development environment is a modest laptop with:

- Intel Core i5-6300U processor.
- 16 GB RAM.
- 256 GB SSD.
- Integrated Intel graphics.
- Zorin OS 18.1.

The solution should prioritize lightweight Python libraries and CPU-based processing.

No GPU-dependent workflow should be introduced without a clear need and approval.

### Budget

The project should prefer:

- Free and open-source libraries.
- Local development tools.
- Free datasets.
- Local database storage.
- Minimal external services.

Paid services are outside the current plan unless explicitly approved.

### Academic Requirements

The application must demonstrate practical use of Python and existing AI/ML libraries.

Training a deep neural network or implementing algorithms from scratch is not a required goal unless the course requirements change.

## 10. Success Criteria

The initial version should satisfy the following conditions:

1. A user can create and manage products.
2. A user can track inventory quantities.
3. A user can record or import sales records.
4. Imported data is validated before processing.
5. The forecasting pipeline can generate predictions.
6. Model performance is evaluated using suitable metrics.
7. The system can calculate restocking recommendations.
8. The dashboard presents useful business information.
9. Core business logic has automated tests.
10. The application can run locally using documented instructions.
11. The project can be demonstrated using prepared sample data.

## 11. Scope Change Rules

Any significant scope change must:

1. Be described clearly.
2. Explain why the change is needed.
3. Identify its impact on time and complexity.
4. Identify affected documentation and modules.
5. Be recorded in `../07-project-management/decisions.md`.
6. Receive user approval before implementation.

Small improvements within an approved feature do not require separate approval.

## 12. Related Documentation

- [Project Overview](project-overview.md)
- [Problem and Solution](problem-and-solution.md)
- [Requirements](requirements.md)
- [Features](../01-product/features.md)
- [Acceptance Criteria](../01-product/acceptance-criteria.md)
- [Implementation Roadmap](../06-development/implementation-roadmap.md)