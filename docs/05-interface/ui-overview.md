# UI Overview

## 1. Purpose

This document defines the general user interface direction for SmartStock AI.

The interface should help users manage products, monitor inventory, review sales activity, understand demand forecasts, and make better restocking decisions.

The application should prioritize clarity, usability, and practical information.

---

## 2. UI Design Goals

The interface should:

- Be simple and easy to navigate.
- Present important inventory information clearly.
- Make business data easy to understand.
- Highlight low-stock products and important alerts.
- Display forecasting results in a readable way.
- Provide clear feedback for user actions.
- Avoid unnecessary visual complexity.

The interface should be suitable for users with limited technical knowledge.

---

## 3. Target User

The initial application targets a small-store owner or inventory manager.

The user should be able to:

- View the current business overview.
- Add and manage products.
- Update inventory information.
- Record sales.
- Import historical sales data.
- Analyze sales trends.
- Generate demand forecasts.
- Review restocking recommendations.

The initial version assumes a simple single-store workflow.

---

## 4. Application Structure

The application uses Streamlit with its built-in navigation
(`st.navigation`), grouped into five sidebar sections:

| Group | Pages |
|---|---|
| Overview | Dashboard |
| Inventory | Products & Inventory, Restocking Recommendations |
| Sales | Sales Management, Sales Analytics |
| Forecasting | Demand Forecast |
| Data | Data Import |

Each navigation entry and every page header carries an icon from the
Material Symbols (Rounded) set (§6), so users can orient themselves
visually as well as by label.

---

## 5. General Layout

The proposed application layout includes:

### Sidebar

Contains:

- Application name and logo or icon.
- Main navigation.
- Optional application information.

### Main Content Area

Contains:

- Page title.
- Short page description.
- Main page content.
- Relevant actions.
- Data tables and visualizations.
- Feedback and validation messages.

### Page Header

Each page should have a clear title describing its purpose.

Important actions should be easy to find.

---

## 6. Visual Direction and Design System

The interface follows a clean dashboard-style design, implemented as a
design system recorded in DEC-064:

### Icons — Material Symbols (Rounded)

All icons come from the Material Symbols (Rounded) library through
Streamlit's native support: navigation entries, page titles
(`st.title(..., icon=...)`), section headings (`st.subheader`),
metrics (`st.metric(icon=...)`), alerts, buttons, download buttons, and
expanders. No emojis appear anywhere in the interface, no icon
dependency was added (Streamlit ships the icon font), and icons carry
Streamlit's built-in accessibility labels. Emojis must not be
introduced back; new icons use `:material/name:` shortcodes or `icon=`
parameters with names validated against Streamlit's icon whitelist.

### Colors — native theme (`.streamlit/config.toml`)

| Token | Light | Dark | Use |
|---|---|---|---|
| Primary | `#2563eb` | `#3b82f6` | Primary actions, links, chart lead color |
| Background | `#ffffff` | `#0f172a` | Content area |
| Secondary background | `#f1f5f9` | `#1e293b` | Secondary surfaces |
| Sidebar background | `#e9eef7` | `#131f36` | Navigation rail |
| Text | `#0f172a` | `#e2e8f0` | Body text |
| Border | `#d3dbe7` | `#334155` | Widget, card, and table borders |
| Green | `#16a34a` | `#4ade80` | Success / In Stock |
| Orange | `#ea580c` | `#fb923c` | Attention / Low Stock |
| Yellow | `#ca8a04` | `#facc15` | Warning |
| Red | `#dc2626` | `#f87171` | Error / Out of Stock |
| Chart palette | brand-led categorical set | brightened set | All charts |

The dark theme (`[theme.dark]`) ships with the app; users switch with
Streamlit's built-in theme toggle (app menu → Settings → Theme: Light /
Dark / Use system setting) — no code or configuration changes needed.

Semantic usage (color carries meaning, never decoration):

- Green — healthy or successful: In Stock, an accepted action.
- Orange — attention required: Low Stock, needs reorder, a missing
  setup step.
- Yellow — caution / estimate: forecast values are estimates, not
  guaranteed outcomes.
- Red — danger: Out of Stock, an action was rejected (a red message
  never changes data).
- Blue — neutral information and guidance.
- Gray — muted secondary context.

### Emphasis layer (DEC-065)

Important data must be visually special, not buried in prose. On top of
the native theme, `src/smartstock/pages/ui.py` ships a small
theme-aware CSS layer (re-reads the active light/dark variant every
render, so it follows `config.toml`):

| Utility | Purpose |
|---|---|
| `hero_stat` | The one most important number on a page, extra large and semantically colored (e.g. the suggested order quantity on Restocking, in orange) |
| `pill` | Small semantic badge for states and cautions (e.g. the yellow "Estimate" pill on forecast results) |
| `strong` | Inline bold value inside a sentence (e.g. the linked dataset item id) |
| `formula_box` | Monospace panel for calculation walk-throughs (restocking expanders) |

Native-side sizing: metric values render at 2.5 rem / weight 700, and
heading icons get explicit sizes (page title 2.5 rem, section headings
proportional), so title → section → number → body scanning is obvious.
Product-table status cells combine the state tint with matching bold
state text. No decorative styling exists; every color and size maps to
a meaning listed above.

### Languages — English default, Arabic toggle (F-020, DEC-066)

The interface is bilingual: English is the default language, and a
sidebar switcher (top of the navigation) flips every page to Arabic
with right-to-left direction. Key facts:

- Switching language is an explicit user action; a fresh session is
  always English, so shared links and the approved test pins stay
  stable.
- All interface strings come from one table in `smartstock/i18n`;
  a test (`tests/test_i18n.py`) enforces that both languages define
  every key, so a half-translated screen cannot happen silently.
- Numerals, SKUs, and decision-reference codes (DEC-xxx, BR-xxx) stay
  in Western digits in v1; URLs stay English regardless of language.
- Rollout is page by page (Dashboard first); a not-yet-translated page
  still renders fully in English in both languages until its pass.

### Visual hierarchy — identify elements by eye

Each interface element type has a distinct, consistent visual shape:

| Element | How it is recognized |
|---|---|
| Primary action | Filled brand-blue button (one per view) |
| Secondary actions | Bordered buttons with icons |
| Navigation | Sidebar rail in a distinct tone, icon + label entries |
| Information cards | Bordered metric cards and bordered dashboard panels |
| Data tables | Banded header row in a distinct background |
| Forms | Bordered field group with a filled primary submit |
| Page position | Icon + title header, section subheaders beneath |

Typography reinforces the hierarchy: heading weights 800/700/600 for
title/section/subsection levels against regular body text, larger
heading sizes (3/2.25/1.75 rem), and metric values at 2.5 rem / weight
700 so the numbers dominate their cards.

### Typography and spacing

Streamlit's default Source Sans family with a 16 px base size; titles,
subheaders, and captions provide the hierarchy (title → subheader →
body/caption). Metric cards use bordered cards with icons; sections are
separated by consistent subheaders; dashboard sections sit inside
bordered panels.

---

## 7. Data Presentation

Data should be presented in the most useful format.

Examples:

| Information | Suggested Presentation |
|---|---|
| Total products | Metric card |
| Current stock | Metric or table |
| Low-stock products | Alert or table |
| Sales trends | Line chart |
| Product performance | Bar chart or table |
| Demand forecasts | Line chart |
| Restocking suggestions | Table |

Avoid displaying too much information in a single section.

Important information should be visible without requiring unnecessary navigation.

---

## 8. User Feedback

The application should provide clear feedback after important actions.

Examples:

- Product created successfully.
- Product updated successfully.
- Inventory adjusted successfully.
- Sale recorded successfully.
- CSV file uploaded successfully.
- Forecast generated successfully.
- Invalid input detected.
- Insufficient historical data.
- Model artifact unavailable.

Messages should explain what happened and what the user can do next when necessary.

---

## 9. Loading and Empty States

The interface should handle situations where data is unavailable.

Examples:

### Empty Products

Display a message explaining that no products have been added yet.

Provide a clear action to add the first product.

### Empty Sales History

Explain that sales records are required for analytics and forecasting.

### No Forecast Available

Explain why a forecast cannot be generated.

Possible reasons:

- Model has not been trained.
- Historical data is unavailable.
- Selected product has insufficient history.

### Loading States

Use appropriate loading indicators for operations that may take noticeable time.

---

## 10. Error States

Errors should be understandable and actionable.

Examples:

- Invalid product information.
- Invalid sales quantity.
- CSV validation failure.
- Database operation failure.
- Model loading failure.
- Forecasting input validation failure.

Avoid exposing raw technical stack traces in the normal user interface.

Technical details may be logged for development purposes.

---

## 11. Tables and Forms

Tables should:

- Use clear column names.
- Display relevant information only.
- Support scrolling when needed.
- Use consistent formatting.
- Highlight important statuses.

Forms should:

- Group related fields.
- Use clear labels.
- Validate inputs.
- Explain required fields.
- Display useful error messages.

Destructive actions should require appropriate confirmation.

---

## 12. Charts and Visualizations

Charts should support business decisions.

Recommended chart types:

- Line charts for sales trends and forecasts.
- Bar charts for product comparisons.
- Tables for detailed inventory information.

Every chart should have:

- A descriptive title.
- Clearly labeled axes.
- Readable values.
- Appropriate date ranges.
- A legend when multiple series are displayed.

Forecast charts should distinguish historical actual values from future predictions.

---

## 13. Responsive Considerations

The initial application is primarily designed for desktop use.

However, the layout should remain usable on smaller screens when practical.

Avoid layouts that depend on many side-by-side columns.

Important tables and forms should remain readable.

---

## 14. UI Scope

The initial UI includes:

- Dashboard.
- Products and inventory management.
- Sales management.
- Sales analytics.
- Demand forecasting.
- CSV import.

Advanced design systems, complex animations, and custom frontend frameworks are not required.

---

## 15. Open Decisions

Resolved (see §6 and DEC-064):

- Final color palette — implemented in `.streamlit/config.toml`.
- Final typography — Streamlit defaults (Source Sans family, 16 px).
- Application logo or icon — `assets/favicon.svg` (package mark on the
  brand-blue tile).
- Exact navigation layout — `st.navigation` with five sidebar groups.
- Whether a dark theme is required — yes, provided since 2026-11-12
  (`[theme.dark]` in `.streamlit/config.toml`, switched with Streamlit's
  built-in theme toggle).
- Detailed chart configurations — Streamlit built-in charts with the
  themed categorical palette.
- Whether table filtering and sorting require custom controls — Streamlit
  dataframe sorting plus the page-level search/filter controls in place.

---

## 16. Related Documentation

- [Pages Specification](pages-specification.md)
- [Dashboard Specification](dashboard-specification.md)
- [Features](../01-product/features.md)
- [User Flows](../01-product/user-flows.md)
- [Acceptance Criteria](../01-product/acceptance-criteria.md)