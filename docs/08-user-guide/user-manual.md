# SmartStock AI — User Manual

A friendly, plain-language guide to using SmartStock AI v1. No programming
knowledge needed — everything here is explained in everyday words.

---

## 1. What is SmartStock AI?

SmartStock AI is a web application that helps you run the inventory side of
a small shop. In one place you can:

- Keep a list of your products and how many units of each you have.
- Record every sale — the stock count updates itself automatically.
- See charts of how your sales are going.
- Ask the app how much demand to expect for the next 7, 14, or 30 days
  (the "AI" part — a forecasting model trained on sales history).
- Get gentle suggestions about which products to restock and how much
  to order.

Two honest promises the app makes to you:

1. **Suggestions, never orders.** The app will never purchase anything or
   change your stock by itself. Every recommendation is advice; you decide.
2. **Forecasts are estimates.** A prediction of "30 units next week" is a
   best guess from history, not a promise. Real life can differ.

---

## 2. Getting started

### 2.1 What you need

- A computer with Python 3.12 installed.
- The SmartStock AI project folder.

### 2.2 Starting the app (first time)

Open a terminal in the project folder and run:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2.3 Starting the app (every time)

```
.venv/bin/python -m streamlit run app.py
```

Your browser opens automatically at a local address (something like
`http://localhost:8501`). Nothing is published to the internet — this is
your private, local application.

### 2.4 Where your data lives

Everything you enter is stored in a small database file:
`data/smartstock.db`. It is created automatically on first run. To back
up your work, copy that file.

### 2.5 One-time setup for forecasting

Demand forecasting needs a trained model. If you have the historical
dataset (`data/raw/train.csv`), train it once:

```
PYTHONPATH=src .venv/bin/python scripts/train_model.py
```

Until the model is trained, every other feature works fine — the app just
tells you that forecasts are not available yet.

### 2.6 Light and dark mode

Click the menu (three dots, top-right) → **Settings** → **Theme** → choose
*Light*, *Dark*, or *Use system setting*. The app ships with both
color schemes; no restart needed.

---

## 3. Words you will see everywhere

| Word | What it means |
|---|---|
| **Product** | Anything you sell. Has a name and a **SKU**. |
| **SKU** | A short unique code for a product (e.g., `TSHIRT-BLU`). No two products share one. |
| **Stock** | How many units of a product you currently have. |
| **Lead time** | How many days it takes a new order to arrive after you place it. |
| **Safety stock** | Extra units you keep "just in case" — a buffer against surprises. |
| **Average daily demand** | How many units of a product sell per day on average, over its most recent sales history (up to 30 days; days with no sales count as zero). |
| **Reorder point** | A danger line. When stock falls to this level or below, it is time to think about ordering. |
| **Dataset item** | An item number from an imported historical CSV file. Linking a product to one is what enables forecasting for it. |
| **Forecast horizon** | How far ahead to predict: 7, 14, or 30 days. |

---

## 4. Tour of the pages

The sidebar on the left is your navigation. The pages are grouped into
**Overview**, **Inventory**, **Sales**, **Forecasting**, and **Data**.

---

### 4.1 Dashboard — your morning glance

*Sidebar → Overview → Dashboard*

The Dashboard answers "how is the shop doing today?" at a glance.

**Top cards:**

- **Active products** — how many products you currently sell.
- **Total stock** — the sum of all units on your shelves.
- **Products needing reorder** — how many products have stock at or below
  their reorder point.

**Second row of cards:**

- **Units sold (last 7 days)** and **Sales recorded (last 7 days)** —
  your recent activity.
- **Top seller (30 days)** — units sold by your best-selling product.

**Below the cards, four panels:**

1. **Sales trend** — a line chart of units sold per day. Use the
   *Last 7 days / Last 30 days* switch above the metrics to change the
   window.
2. **Top sellers — last 30 days** — a ranked table of your best products.
3. **Low-stock overview** — a warning listing every product that is
   Out of Stock or Low Stock, with suggested order quantities. If
   everything is healthy, you see a green "All products are In Stock"
   message instead.
4. **Forecast readiness** — how many of your products can actually be
   forecast (they need a linked dataset item, explained in §4.6).

The Dashboard is read-only — it is a window, not a workspace.

---

### 4.2 Products & Inventory — where products live

*Sidebar → Inventory → Products & Inventory*

This page has four tabs across the top:

**Product list** — a table of all active products with name, SKU,
category, stock, lead time, safety stock, reorder point, average daily
demand, and a color-coded **Status** column:

| Status | Meaning |
|---|---|
| **In Stock** (green) | Stock is above the reorder point. Relax. |
| **Low Stock** (orange) | Stock is above zero but at or below the reorder point. Start thinking about an order. |
| **Out of Stock** (red) | Stock is zero. Act now. |

Above the table: a **search box** (matches name or SKU, ignores upper/lower
case) and **filters** for Category and Stock status.

**Add product** — create a new product:

- *Name* and *SKU* are required; the SKU must be unique.
- *Category* is optional.
- *Initial stock* is what you have on hand right now (default 0).
- *Lead time* defaults to 3 days; *safety stock* defaults to 0.

**Edit product** — change an existing product's details, including lead
time and safety stock. This tab also contains two special actions:

- **Deactivate product** (soft delete): the product disappears from
  listings and can no longer be sold, but its sales history is kept and
  you can bring it back anytime. You must tick a confirmation box first.
- **Reactivate product**: available when you select a deactivated product.

Also in this tab: **Linked dataset item** — see §4.6 for why it matters.

**Adjust stock** — change stock for reasons other than a sale:

- *Add or remove units*: for a delivery that arrived (+), damaged or
  lost goods (−), or any normal correction. Enter a number (positive or
  negative) and press **Apply adjustment**.
- *Set exact stock (correction)*: overwrites the stored count with a
  number you type (e.g., after a physical stock count). The app warns you
  because this erases the previous value — prefer "Add or remove units"
  for everyday changes.

Stock can never go below zero. An adjustment that would make it negative
is rejected with a clear message.

---

### 4.3 Sales Management — recording what you sell

*Sidebar → Sales → Sales Management*

Two tabs:

**Record sale** — log a sale:

1. Pick the product (each option shows its available stock).
2. Enter the quantity (must be at least 1, whole units).
3. Pick the sale date. You may backdate (e.g., you sold it yesterday and
   are entering it today), but future dates are not accepted.
4. Press **Record sale**.

What happens next: the stock for that product is reduced automatically,
and a green confirmation tells you the remaining stock.

Two protections worth knowing:

- **Not enough stock?** If you try to sell more units than you have, the
  sale is rejected — nothing is recorded and stock stays unchanged. The
  message tells you both what you asked for and what was available.
  (Recording more stock first, via *Adjust stock*, is the correct move.)
- Deactivated products do not appear in the picker.

**Sales history** — browse everything you have recorded, filterable by
product and by date range (untick *All time* to choose From/To dates).
Each row shows product, quantity, sale date, and when it was entered.
Sales records are permanent — there is no edit or delete, which keeps
history trustworthy.

---

### 4.4 Sales Analytics — understanding your sales

*Sidebar → Sales → Sales Analytics*

Pick a start date, an end date, and (optionally) a single product, and the
page shows:

- **Four summary cards:** Units sold, Sales recorded, Avg units/day
  (days without sales count as zero), and Days with sales.
- **Daily units sold** — a line chart of the selected range.
- **Weekday pattern** — a bar chart of the average units sold on each day
  of the week. Handy for spotting "Saturdays are busy" effects.
- **Sales by product** — a ranking with each product's share of total
  units.
- **Product performance** — units sold, daily average, first and last
  sale in the range, and a simple **Trend** column (Rising/Falling/Stable,
  comparing the first half of your range with the second half).
- **Monthly totals** — a month-by-month table when your range spans
  several months.

**Downloads:** three CSV export buttons — *sales by product*,
*product performance*, and *monthly totals*. The files open in any
spreadsheet program.

Note: everything here is counted in **units**, not money. The app does not
store prices in v1, so it will never guess at revenue.

---

### 4.5 Demand Forecast — the AI part

*Sidebar → Forecasting → Demand Forecast*

This page predicts how many units a product will sell in the coming days.

**How to use it:**

1. Choose a product.
2. Choose a horizon: **Next 7 days** (default), **Next 14 days**, or
   **Next 30 days**.
3. Press **Generate forecast**.

**What you get:**

- A yellow **Estimate** badge (yellow always means "caution — this is
  an estimate, not a promise").
- Total expected demand for the window and the average per day.
- A day-by-day table of predicted demand.
- The method used, which is one of two:

| Your history | Method | Meaning |
|---|---|---|
| 31+ observed days | **Random Forest model** | The trained machine-learning model, using patterns like day-of-week and recent averages. |
| 1–30 observed days | **Trailing 7-day average** | A simpler method: recent sales repeated forward. Honest when history is short. |
| 0 observed days | No forecast | You get a clear "no suitable history" message instead of a made-up number. |

**The one thing you must do first:** a product can only be forecast when
it is linked to an imported dataset item. On the **Edit product** tab of
Products & Inventory, tick *"Forecast via a linked dataset item"* and enter
the item number whose imported history matches that product. The forecast
page then uses that item's sales history to predict.

**"How accurate is the model?"** — the section at the bottom shows real,
measured accuracy numbers from the model's training evaluation (MAE —
mean absolute error — and RMSE, in units per product-day; lower is
better). For context: the model's average error is about 6 units per
product-day, versus about 10.5 for a naive "copy last value" approach and
8.4 for a simple weekly average — the model clearly beats the simple
baselines. These are stored, measured values, not live calculations.

Reminder the app itself shows: forecasts are estimates, not guarantees.

---

### 4.6 Data Import — bringing in history

*Sidebar → Data → Data Import*

If you already track sales elsewhere (e.g., a spreadsheet or an old
system), import that history here. This is what powers the forecasting
model.

**The format is strict — four columns, exactly these names:**

```csv
date,store,item,sales
2016-01-01,1,1,12
2016-01-02,1,1,9
```

- `date` — `YYYY-MM-DD`.
- `store` — the app is single-store; **only store 1 rows are imported**.
  Rows for other stores are counted as "Other stores" and skipped.
- `item` — the item number. This becomes the "dataset item" you link
  products to.
- `sales` — units sold that day (non-negative).
- No extra columns, no missing columns.

**How the page works — nothing is stored until you confirm:**

1. Upload the CSV. The app validates it and shows a **preview**:
   rows in file, valid for store 1, rejected rows, other-store rows, the
   date range, and a sample of accepted records.
2. Problem rows are explained in expanders ("Rejected rows" and
   "Within-file duplicates") with the row number and the reason — bad
   dates, negative sales, missing values, repeated item-and-date pairs.
3. If the file is importable, press **Import N record(s)**. The accepted
   rows are stored in one transaction — either everything valid goes in
   or nothing does. There is never a half-finished import.
4. A summary shows what was stored, what was skipped, and the batch
   number. A **Previous imports** expander lists every past batch.

Two important behaviors:

- **Re-uploading the exact same file is rejected** (recognized by its
  digital fingerprint), so you cannot accidentally import it twice.
  To add more data, upload a different file.
- **Imports never change current stock.** Historical records only feed
  analysis and forecasting; your live inventory is untouched.

---

### 4.7 Restocking Recommendations — what should I order?

*Sidebar → Inventory → Restocking Recommendations*

This is the page that turns your data into advice. It is entirely
**advisory**: nothing is ordered, and your stock is never changed here.

**Top cards:** how many products need reorder, how many have usable
recommendations, and how many lack enough data yet.

**"Consider restocking" table** — every product whose stock is at or
below its reorder point, with all the inputs side by side: stock,
average daily demand, lead time, safety stock, reorder point, target
stock, and the suggested **Order** quantity.

**The reasoning behind every number** — each product has a lightbulb
expander that leads with the suggested order in big orange digits
(orange = this needs your attention) and then walks you through the
calculation in a step-by-step panel, so you can always check the advice
instead of trusting it blindly.

**How the advice is calculated (simple version):**

- *Reorder point* = (average daily demand × lead time) + safety stock.
- *Target stock* = (average daily demand × (lead time + 7)) + safety
  stock — enough to cover the wait for delivery plus a 7-day cushion.
- *Order quantity* = target stock − current stock (never negative; if
  you already have enough, it says 0).

*Worked example:* a product sells 3 units a day, deliveries take 5 days,
safety stock is 10.

- Reorder point = 3 × 5 + 10 = **25** → worry when stock hits 25.
- Target stock = 3 × (5 + 7) + 10 = **46**.
- With 20 units in stock → order 46 − 20 = **26 units**.

A product needs at least one recorded sale to get recommendations;
otherwise it appears in "Not available yet" with the reason.

**Download:** an *Export recommendations (CSV)* button saves the whole
table for your supplier spreadsheet.

---

## 5. Common tasks, step by step

### 5.1 Set up your shop on day one

1. **Products & Inventory → Add product**: one product per SKU, with
   realistic lead time and safety stock, and your on-hand units as
   Initial stock.
2. **Data Import**: if you have old sales history in CSV form, import it
   now (§4.6).
3. **Edit product → tick "Forecast via a linked dataset item"**: connect
   each product to its imported item number.
4. **Sales Management**: start recording sales the same day.

### 5.2 A sale just happened

Sales Management → Record sale → pick product, quantity, date →
**Record sale**. Stock updates itself. Done.

### 5.3 A delivery arrived

Products & Inventory → Adjust stock → *Add or remove units* → positive
number → **Apply adjustment**.

### 5.4 My stock count is wrong

Do a physical count, then Products & Inventory → Adjust stock →
*Set exact stock (correction)* → enter the true count → **Set stock
level**. (Use this for corrections only; everyday changes should use
Add/remove.)

### 5.5 Should I order anything today?

1. Dashboard → check *Products needing reorder*.
2. Restocking Recommendations → read the table and the explanation
   expanders.
3. Decide, order from your supplier, and when the goods arrive record
   them via Adjust stock (§5.3).

### 5.6 Why can't I forecast product X?

Check, in order:

1. Is it **linked to a dataset item**? (Edit product tab.)
2. Has history for that item been **imported**? (Data Import →
   Previous imports.)
3. Does the item have **at least 1 observed day** of sales?
4. Is the model **trained**? (§2.5 — the page tells you if not.)

---

## 6. Rules the app enforces (and why)

These are not obstacles — they protect your data:

| You tried to… | The app… | Why |
|---|---|---|
| Sell more units than you have | Rejected the sale | Never invents negative stock; a sale only happens if it really happened. |
| Sell a deactivated product | Rejected | Inactive products are retired; history stays, selling stops. |
| Enter a future sale date | Rejected | The app records the past, not planned transactions. |
| Enter a zero or negative sale quantity | Rejected | A "sale" of zero units is not a sale. |
| Adjust stock below zero | Rejected | Same no-negative-stock rule. |
| Delete a product | Soft delete only | History is preserved; the action is reversible. |
| Import a CSV with wrong columns or bad rows | Rejected the bad rows with reasons | Invalid data never becomes valid silently. |
| Import the same file twice | Rejected the second time | Prevents accidental double-counting. |
| Use revenue figures | Not available | No price data is stored, so no revenue is ever guessed. |

---

## 7. Reading the app's messages

| Message type | What it means |
|---|---|
| Green confirmation | The action succeeded — it tells you exactly what changed. |
| Orange/yellow warning | Attention needed, nothing broken (e.g., low stock, a correction overwrites data). Yellow specifically marks **estimates**: forecast numbers and other advisory values. |
| Red error | The action was **not** performed. Nothing half-happened; fix the problem and retry. |
| Blue info | A neutral explanation (e.g., a product cannot be forecast yet, and why). |

A golden rule of this app: **a red message never changes your data.**

---

## 8. Frequently asked questions

**Q: Can the app order products for me?**
No — by design. It suggests; you decide and order through your supplier.

**Q: Can I have two shops / branches?**
Not in this version. The app is built for one store, and imports keep
only store 1 rows.

**Q: Can I undo a sale?**
Sales are permanent so history stays honest. If a sale was entered by
mistake, correct the stock via *Adjust stock* on the Products &
Inventory page.

**Q: Why does the forecast say "trailing 7-day average fallback"?**
The product has fewer than 31 days of observed history — too little for
the full model. The app uses recent sales as a simple, honest estimate
and switches to the Random Forest automatically once 31+ days exist.

**Q: Are the accuracy numbers on the forecast page calculated live?**
No. They are the measured results from the model's evaluation during
training, shown as-is so you know how much to trust forecasts.

**Q: Where are prices and profit?**
Not in this version. Everything is counted in units. Revenue analytics
would need reliable price data.

**Q: Is my data sent anywhere?**
No. The app runs on your machine and stores everything in a local
database file.

**Q: The forecast button says the model artifact is missing.**
The model has not been trained on this installation. See §2.5.

---

## 9. Glossary

| Term | Plain meaning |
|---|---|
| MAE | Mean Absolute Error — on average, how many units off a prediction is. Lower is better. |
| RMSE | Root Mean Squared Error — like MAE but punishes big mistakes more. Lower is better. |
| Baseline | A simple comparison method (e.g., "same as last week"). The AI model must beat it to be worth using. |
| Soft delete | Deactivating rather than erasing — history is kept, reversal is possible. |
| Batch (import) | One completed import run, numbered for reference. |
| Fingerprint | A digital identity of a file, used to recognize re-uploads. |
| CSV | A plain table file that spreadsheet programs open and save. |

---

## 10. Where to learn more

- Product rules and exact formulas: `docs/01-product/business-rules.md`
- Screen-by-screen specification: `docs/05-interface/pages-specification.md`
- Design and appearance (colors, icons, dark theme):
  `docs/05-interface/ui-overview.md`
- How the forecasting model works:
  `docs/04-machine-learning/forecasting-strategy.md`
