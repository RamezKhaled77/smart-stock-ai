# Problem and Solution

## 1. Purpose

This document explains the business problem SmartStock AI aims to address, the limitations of common inventory practices, and the proposed solution.

It defines the reasoning behind the project and provides a reference for product and technical decisions.

## 2. Business Context

Inventory management is an important part of running a retail business.

A business needs enough products to satisfy customer demand without keeping excessive quantities that increase storage costs and tie up available capital.

Small businesses may not have dedicated inventory planning tools or employees responsible for demand analysis.

They often rely on:

- Manual stock counting.
- Spreadsheets.
- Personal experience.
- Basic sales records.
- Simple minimum-stock alerts.

These methods may work for a small number of products, but they become less effective as the product catalog and sales history grow.

## 3. Core Problems

### 3.1 Stockouts

A stockout happens when a product is unavailable while customers want to purchase it.

Possible consequences:

- Lost sales.
- Customer dissatisfaction.
- Missed business opportunities.
- Reduced customer trust.

A business may discover a shortage only after the product has already run out.

### 3.2 Overstocking

Overstocking happens when a business keeps more inventory than it reasonably needs.

Possible consequences:

- Unnecessary storage costs.
- Money tied up in unsold products.
- Increased risk of product damage or expiration.
- Difficulty managing available storage space.

### 3.3 Unpredictable Demand

Product demand may change over time.

Examples include:

- Weekly sales patterns.
- Monthly changes.
- Seasonal demand.
- Sudden increases or decreases.
- Differences between individual products.

Without analyzing historical sales, it may be difficult to recognize these patterns.

### 3.4 Manual Decision-Making

Some businesses decide when to reorder based on personal experience or fixed stock thresholds.

These methods may ignore:

- Historical demand.
- Recent sales changes.
- Expected future demand.
- Supplier lead time.
- Safety stock requirements.

### 3.5 Limited Sales Insights

Sales records contain useful information, but many small businesses do not analyze them effectively.

They may not know:

- Which products sell the most.
- Which products have declining demand.
- How demand changes over time.
- Which products may require additional stock soon.

## 4. Root Causes

The main causes behind these problems may include:

1. Lack of structured sales data.
2. Limited use of historical sales information.
3. Manual inventory tracking.
4. Lack of forecasting tools.
5. Poor visibility into future inventory requirements.
6. Lack of clear restocking rules.

These causes are project hypotheses and should be validated against the intended users and available data.

## 5. Proposed Solution

SmartStock AI proposes combining inventory management with demand forecasting.

The system will:

1. Maintain product and inventory information.
2. Store historical sales records.
3. Analyze sales patterns.
4. Forecast future demand.
5. Compare expected demand with available stock.
6. Generate restocking recommendations.
7. Display useful summaries and alerts.

The objective is to help users make better decisions, not to automate every business decision.

## 6. How the Solution Addresses Each Problem

| Business Problem | Proposed System Capability |
|---|---|
| Stockouts | Low-stock monitoring and demand-based recommendations |
| Overstocking | Forecast-based replenishment planning |
| Unpredictable demand | Historical sales analysis and forecasting |
| Manual decisions | Data-driven inventory insights |
| Limited sales visibility | Dashboard and sales analytics |

These capabilities describe the intended solution. Their effectiveness must be evaluated during development and testing.

## 7. Example Business Scenario

Consider a small shop that sells several products.

The owner notices that one product sells more frequently during weekends.

Without a forecasting system, the owner may reorder a fixed quantity every week.

SmartStock AI aims to improve this process:

1. The owner records daily sales.
2. The system analyzes the product's historical demand.
3. The forecasting model estimates upcoming demand.
4. The system checks current inventory.
5. The inventory logic considers the expected demand and replenishment lead time.
6. The system recommends an appropriate restocking quantity.
7. The owner reviews the recommendation before taking action.

The example is illustrative. Actual recommendations depend on validated data and approved business rules.

## 8. Role of Artificial Intelligence

Machine learning is used to estimate future demand based on historical information.

The forecasting component should identify useful patterns in sales data.

Possible input features include:

- Day of the week.
- Month.
- Historical sales.
- Recent average sales.
- Previous sales periods.

The model will produce estimated future demand.

The forecasting process is documented separately in:

`../04-machine-learning/`

## 9. Role of Traditional Business Logic

Machine learning alone cannot determine the correct quantity to purchase.

A business also needs information such as:

- Current stock.
- Expected demand.
- Supplier lead time.
- Safety stock.
- Existing incoming orders, if supported.

The business logic combines these values to produce recommendations.

A simplified reorder point may be:

`Reorder Point = Average Daily Demand × Lead Time + Safety Stock`

A simplified order quantity may be:

`Order Quantity = max(0, Target Stock - Current Stock - Incoming Stock)`

The final formulas, assumptions, and edge cases must be defined in:

`../01-product/business-rules.md`

## 10. Expected Benefits

Potential benefits include:

- Better inventory visibility.
- More informed restocking decisions.
- Reduced risk of stockouts.
- Better control over excess inventory.
- Improved understanding of sales patterns.
- More efficient inventory planning.

These are expected benefits, not guaranteed outcomes.

The project should avoid claiming measurable business improvements without real-world evidence.

## 11. Limitations

The proposed solution has important limitations:

- Forecasting quality depends on historical data quality.
- New products may not have enough sales history.
- Unexpected events may change demand.
- Promotions and price changes may affect sales.
- Supplier lead times may change.
- Forecasts are estimates, not guarantees.
- The initial dataset may not represent every real retail business.

The application must communicate uncertainty and avoid presenting predictions as guaranteed results.

## 12. Validation Questions

The following questions should be considered before finalizing the product:

1. Do target users currently track inventory manually?
2. How do they decide when to reorder?
3. What inventory information is realistically available?
4. Are historical sales records available?
5. How frequently do stockouts happen?
6. Are supplier lead times known?
7. Do users need monetary sales analysis or only quantities?
8. Would users trust and understand forecasting recommendations?

These questions may guide future product validation.

## 13. Related Documentation

- [Project Overview](project-overview.md)
- [Goals and Scope](goals-and-scope.md)
- [Requirements](requirements.md)
- [Business Rules](../01-product/business-rules.md)
- [Forecasting Strategy](../04-machine-learning/forecasting-strategy.md)