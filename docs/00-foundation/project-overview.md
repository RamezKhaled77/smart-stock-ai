# SmartStock AI — Project Overview

## 1. Introduction

SmartStock AI is a Smart Inventory and Demand Forecasting System designed to help small businesses manage inventory and make better stock-related decisions.

The system combines traditional inventory management with data analysis and machine learning-based demand forecasting.

It aims to transform historical sales records into useful insights that help business owners understand product demand, monitor stock levels, and plan future replenishment.

The application is intended to be simple enough for small businesses while demonstrating practical applications of Python, data analysis, and machine learning.

## 2. Project Vision

The vision of SmartStock AI is to make inventory planning more informed and accessible to small businesses.

Instead of relying only on manual calculations or personal experience, users should be able to use historical sales data to understand demand patterns and make more informed inventory decisions.

The system should not replace business judgment. It should provide useful information and recommendations that support it.

## 3. Project Summary

| Item | Description |
|---|---|
| Project Name | SmartStock AI |
| Full Name | Smart Inventory and Demand Forecasting System |
| Project Type | Business-oriented AI application |
| Application Type | Web-based application |
| Primary Language | Python |
| Initial Target | Small businesses and retail shops |
| Main Domain | Inventory Management |
| AI Application | Demand Forecasting |
| Interface | Proposed: Streamlit |
| Database | Proposed: SQLite |
| Project Status | Documentation and Planning |

Technology choices are tracked in `../../02-architecture/tech-stack.md`.

## 4. The Problem

Small businesses often face difficulties managing inventory effectively.

Common problems include:

- Running out of products when customers need them.
- Keeping more stock than necessary.
- Not understanding which products sell frequently.
- Having difficulty predicting future demand.
- Making restocking decisions without sufficient data.
- Spending time analyzing sales records manually.

These problems may lead to lost sales, unnecessary inventory costs, and poor planning.

More details are documented in `problem-and-solution.md`.

## 5. Proposed Solution

SmartStock AI will provide a centralized application for managing products, inventory, and sales.

The system will analyze historical sales data and use forecasting models to estimate future product demand.

Based on demand forecasts and inventory information, it will generate restocking recommendations.

The main workflow is:

1. The user manages products and their inventory information.
2. The user records sales or imports historical sales data.
3. The system validates and processes the sales information.
4. The forecasting component analyzes historical demand.
5. The model predicts future demand.
6. The inventory logic compares expected demand with available stock.
7. The system generates alerts and restocking recommendations.
8. The user reviews the results and makes the final decision.

## 6. Main System Capabilities

The planned system is expected to support:

### 6.1 Inventory Management

- Create and update products.
- View product information.
- Track current stock quantities.
- Monitor low-stock products.
- Manage basic inventory information.

### 6.2 Sales Management

- Record sales.
- View sales history.
- Import sales data from CSV files.
- Analyze sales trends.

### 6.3 Demand Forecasting

- Process historical sales records.
- Generate demand-related features.
- Train and evaluate forecasting models.
- Predict future product demand.
- Display actual and predicted demand.

### 6.4 Inventory Recommendations

- Identify products that may run out of stock.
- Calculate estimated replenishment needs.
- Recommend restocking quantities.
- Explain why a product needs attention.

### 6.5 Dashboard and Reporting

- Display important inventory indicators.
- Summarize sales performance.
- Show demand trends.
- Highlight products requiring attention.
- Present forecasting and recommendation results.

The detailed feature list is maintained in `../01-product/features.md`.

## 7. Intended Users

The initial system targets small retail businesses that:

- Sell physical products.
- Maintain a product catalog.
- Record sales transactions.
- Need to monitor stock quantities.
- Have historical sales information or can start collecting it.

The initial version assumes a single business environment.

The system is not initially designed for large enterprise supply chains or complex multi-warehouse operations.

## 8. Project Context

This project is developed as a practical academic project for an AI and Python course.

The project should demonstrate the use of existing Python libraries to solve a practical business problem.

The academic requirements should be satisfied through:

- Data preparation and analysis.
- Use of machine learning libraries.
- Model training and evaluation.
- Practical application integration.
- Clear presentation of results.

The project does not require implementing machine learning algorithms from scratch or developing deep neural networks unless future requirements justify them.

## 9. Technical Direction

The initial technical direction is:

| Responsibility | Proposed Tool |
|---|---|
| Application | Streamlit |
| Programming | Python |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| Visualization | Plotly |
| Database | SQLite |
| Model Persistence | Joblib |
| Testing | Pytest |

These technologies remain subject to technical review.

See `../../02-architecture/tech-stack.md`.

## 10. Machine Learning Direction

The main AI capability is demand forecasting.

The system will investigate supervised regression models using historical sales data.

Potential approaches include:

- Baseline forecasting methods.
- Linear Regression.
- Random Forest Regression.
- Other suitable models if supported by experiments.

The model should be evaluated using chronological validation and appropriate forecasting metrics.

The final model must be selected based on measured performance and practical usefulness.

See `../../04-machine-learning/forecasting-strategy.md`.

## 11. Important Design Principle

SmartStock AI separates three responsibilities:

### Demand Forecasting

Estimates how much of a product customers may demand in a future period.

### Inventory Management

Tracks the quantity of products currently available.

### Restocking Recommendations

Combines predicted demand with inventory information and business rules to suggest when and how much to reorder.

These responsibilities must remain logically separate.

A demand prediction is not the same as a restocking quantity.

## 12. Project Boundaries

The initial project focuses on:

- Single-business inventory management.
- Product and sales records.
- Historical sales analysis.
- Demand forecasting.
- Basic restocking recommendations.
- A web-based dashboard.

The following are not part of the initial scope unless explicitly approved:

- Multi-branch inventory management.
- Complex supplier integrations.
- Automated purchase order execution.
- Payment processing.
- Accounting systems.
- ERP integrations.
- Mobile applications.
- Advanced deep learning systems.
- Cloud-based enterprise infrastructure.

See `goals-and-scope.md`.

## 13. Success Criteria

The project will be considered successful when:

1. Users can manage products and inventory information.
2. Users can record or import sales data.
3. The system can validate and process historical sales data.
4. At least one forecasting model can be trained and evaluated.
5. The system can generate future demand predictions.
6. Inventory rules can generate useful restocking recommendations.
7. Users can understand the results through the interface.
8. The application works reliably with the prepared demonstration dataset.
9. The main functionality is covered by appropriate tests.
10. The project can be demonstrated and explained clearly.

Detailed measurable acceptance criteria will be maintained in `../01-product/acceptance-criteria.md`.

## 14. Current Assumptions and Open Questions

The following items are not yet fully confirmed:

| Item | Current Status | Notes |
|---|---|---|
| Streamlit | Proposed | Evaluate interface suitability |
| SQLite | Proposed | Confirm database requirements |
| Kaggle Store Item Demand Dataset | Proposed | Inspect data and competition context |
| Random Forest | Proposed | Must be compared against baselines |
| Forecast Horizon | Open Question | Decide how many future days to predict |
| Inventory Lead Time | Open Question | Determine how lead time is represented |
| Safety Stock | Open Question | Define calculation and user configuration |
| Product Categories | Open Question | Decide whether categories are required |
| Sales Input Method | Proposed | Manual entry and CSV import |
| Currency | Open Question | Define whether prices and monetary reporting are required |

The agent must not treat these items as accepted decisions.

## 15. Related Documentation

- [Problem and Solution](problem-and-solution.md)
- [Goals and Scope](goals-and-scope.md)
- [Requirements](requirements.md)
- [Glossary](glossary.md)
- [Features](../01-product/features.md)
- [Technical Stack](../02-architecture/tech-stack.md)
- [Forecasting Strategy](../04-machine-learning/forecasting-strategy.md)