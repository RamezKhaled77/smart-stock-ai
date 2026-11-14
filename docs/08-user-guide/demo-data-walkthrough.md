# Demo Data Walkthrough — `demo_sales_history.csv`

This guide walks you through filling the app with a realistic demo
dataset and explains exactly what you should see on every page as you
go. It is a companion to the user manual
(`docs/08-user-guide/user-manual.md`): the manual explains the pages,
this file gives you a ready-to-run story with expected results.

The dataset is **dummy data shaped to feel real** — a seeded generator
(`scripts/generate_demo_data.py`) produced a plausible year of trading
for five products. No real customer data is involved. It was verified
against the app's real import validator on 2026-11-14: all 1,621 rows
accepted, zero rejected, zero duplicates.

---

## 1. The dataset at a glance

File: `data/samples/demo_sales_history.csv` — the exact format the
Data Import page expects (`date,store,item,sales`), store 1 only
(DEC-015), dates 2025-10-10 → 2026-11-13.

| Item | Story | Rough daily demand | History |
|---|---|---|---|
| 10 | Morning coffee beans — steady seller, busier on Friday/Saturday | ~9 units/day | 400 days |
| 11 | Neighborhood bread — high volume with a strong weekly rhythm | ~16–18 units/day | 400 days |
| 12 | Summer iced tea — hot months double the demand, winter slows it | ~6 units/day | 400 days |
| 13 | Protein bars — a product that caught on: it grows all year | ~7 overall, ~10 lately | 400 days |
| 14 | New snack — only three weeks on the shelf | ~4 units/day | 21 days |

Item numbers deliberately start at 10 so this file can never collide
with the small manual-test samples (items 1, 2, 3, 7) through the
database's unique item+date rule (DEC-053).

**One concept this demo teaches** — the app has two kinds of sales
data, and they feed different pages:

- **Imported history** (this file) is *forecasting fuel*. Only the
  Demand Forecast page uses it.
- **Recorded sales** (what you key into Sales Management) drive the
  Dashboard activity metrics, the restocking formulas, and the Sales
  Analytics page.

That is why this walkthrough has you do both: import the history, and
record a short burst of recent sales.

---

## 2. Step 1 — Import the file

Run the app, open **Data Import**, upload
`data/samples/demo_sales_history.csv`.

Before confirming, the preview should show:

- **Rows in file:** 1,621
- **Valid for store 1:** 1,621
- **Rejected (invalid):** 0
- **Other stores:** 0
- A caption with the accepted date range: 2025-10-10 → 2026-11-13
- A fingerprint caption (the file's SHA-256 identity, DEC-053)
- A preview table of the first accepted rows

Then confirm the import. You should see a success flash and the
**Import history** table gains a row for this batch. Importing the
*same file again* is rejected with a "This exact file was already
imported…" error — that is the fingerprint check working, not a
failure (DEC-053).

---

## 3. Step 2 — Create the five products

On **Products & Inventory → Add product**, create these five products.
The **linked dataset item** (Edit-product tab after creation, DEC-060)
is what connects a product to its imported history for forecasting.

| Product name | SKU | Linked item | Opening stock | Lead time | Safety stock |
|---|---|---|---|---|---|
| Morning Coffee Beans 250g | `DEMO-COFFEE` | 10 | 100 | 3 | 2 |
| Neighborhood Bakery Bread | `DEMO-BREAD` | 11 | 250 | 2 | 5 |
| Summer Iced Tea 1L | `DEMO-TEA` | 12 | 67 | 4 | 3 |
| Protein Bar Choco 40g | `DEMO-BARS` | 13 | 124 | 3 | 4 |
| New Snack Mix 100g | `DEMO-NEW` | 14 | 64 | 3 | 2 |

The opening stocks are sized to cover the ten-day sales burst in the
next step *and* land in the intended state afterwards: coffee, tea,
and bars end at or below their reorder points, while bread and the new
snack stay healthy. (Opening stock well below what you intend to sell
would trip the insufficient-stock rejection — which is itself a rule
worth seeing once, deliberately, in the experiments section.)

Right after creation, the product table reads **In Stock** for all
five — the stock-status context needs demand, which arrives with the
recorded sales in the next step.

---

## 4. Step 3 — Record a burst of recent sales

The restocking formulas, the Dashboard's activity metrics, and Sales
Analytics all run on **recorded** sales. To bring those pages alive,
record the following backdated sales on **Sales Management** (dates
assume you do this around 2026-11-14; backdating is allowed, future
dates are rejected — DEC-051).

Ten sales per product, one per day, 2026-11-05 → 2026-11-14:

| Date | Coffee | Bread | Tea | Bars | New snack |
|---|---|---|---|---|---|
| 2026-11-05 | 12 | 18 | 7 | 11 | 4 |
| 2026-11-06 | 8 | 15 | 5 | 10 | 3 |
| 2026-11-07 | 9 | 14 | 6 | 12 | 5 |
| 2026-11-08 | 10 | 17 | 8 | 9 | 4 |
| 2026-11-09 | 7 | 12 | 4 | 11 | 3 |
| 2026-11-10 | 11 | 16 | 6 | 10 | 4 |
| 2026-11-11 | 9 | 15 | 5 | 9 | 5 |
| 2026-11-12 | 8 | 18 | 7 | 12 | 3 |
| 2026-11-13 | 10 | 20 | 6 | 10 | 4 |
| 2026-11-14 | 6 | 15 | 5 | 10 | 4 |

Each successful sale flashes green and the stock metric drops by the
quantity. After the burst, the product table's **Status** column reads
**Low Stock** (orange) for coffee (10 left, reorder point ~29), tea
(8, ~27), and bars (20, ~36), and **In Stock** (green) for bread and
the new snack.

If you skip this step the app still works — the Dashboard and restock
advice simply wait for your first real sale (restocking says "No sales
are recorded for this product yet…" rather than inventing a
zero-demand answer, DEC-031).

---

## 5. What you should see, page by page

### Dashboard

- **Active products: 5**, **Total stock: 605** right after creation
  (100 + 250 + 67 + 124 + 64), dropping to **≈ 153** once the step-4
  sales are recorded (452 units sold)
- **Needing reorder: 3** (coffee, tea, bars)
- **Last-7-days units** reflecting the recorded sales (the last 7 rows
  of the table above — about 310 units across all products)
- The **sales trend chart** fills with the recorded days
- **Low-stock overview** lists coffee, tea, and bars with a suggested
  order quantity each
- **Forecast readiness: 5 of 5** products linked to imported history

### Restocking Recommendations

Three products appear under "Needs attention" — coffee, tea, and bars
— each with:

- A large orange **suggested order number** (the hero stat)
- A monospace formula panel showing the walk-through: average daily
  demand over the recorded window, reorder point
  `ceil(demand × lead time) + safety`, target stock
  `ceil(demand) × (lead time + 7) + safety`, and
  `max(0, target − stock)` for the order size (DEC-032/038/033)

Approximate figures with the numbers above (the app recomputes from
your actual data, so expect close-but-not-identical values; stock
shown is what remains after the step-4 burst):

| Product | ~Demand/day | ~Reorder point | ~Target stock | Stock left | ~Suggested order |
|---|---|---|---|---|---|
| Coffee | 9.0 | 29 | 92 | 10 | ~82 |
| Bread | 16.0 | 37 | 149 | 90 | — not listed |
| Tea | 5.9 | 27 | 69 | 8 | ~61 |
| Bars | 10.4 | 36 | 114 | 20 | ~94 |
| New snack | 3.9 | 14 | 42 | 25 | — not listed |

The **Export recommendations (CSV)** button downloads exactly the
advice shown. Bread and the new snack should not appear — they are
above their reorder points, and the app only advises when there is a
decision to make (BR-022, advisory DEC-031).

### Demand Forecast

Pick any product and a horizon (7 / 14 / 30 days):

- **Coffee, bread, tea, bars** → forecast built by the **Random
  Forest** model, with a caption confirming the method (≥ 31 observed
  days, DEC-058)
- **New snack** → the **Trailing 7-day average** fallback, also stated
  in a caption — fewer than 31 observed days means the honest simple
  estimate, not the full model
- **Horizons change the table length** (7, 14, or 30 future days)
- The **"How accurate is the model?"** section shows the stored
  training-time metrics: validation MAE 6.033 / RMSE 7.785, test MAE
  6.088 / RMSE 7.910, with the naive (MAE 10.512) and 7-day-average
  (MAE 8.378) baselines for context (DEC-062). Important: these
  numbers describe the model's accuracy on its training dataset, not
  a guarantee for your store.
- Products whose forecast cannot be produced show a plain-language
  reason — never a crash and never a silent zero.

### Sales Analytics

With the step-4 sales recorded (a ~10-day range):

- **Totals:** 50 sales, roughly 450 units across the five products
- **Product ranking:** bread first (~160 units), then bars ~104,
  coffee ~90, tea ~59, new snack ~39 — with each product's share
- **Daily trend chart** over the recorded days
- **Weekday pattern chart** — five weekdays' worth of rhythm
- **Product performance table:** units, average per day, first/last
  sale, and a trend label per product. **Protein bars should read
  "Rising"** (its growth story shows even in ten days); most others
  read "Steady"; a product with sales only in the newer half would
  read "Rising (new)"
- All three **CSV export buttons** download files matching the tables
  on screen (DEC-063)

Try widening the date range back to 2026-10-15: the totals stay the
same (recorded sales only go back to 11-05) and the "days in range"
metric grows — a good check that the range filter works.

### Products & Inventory — experiments

Each of these is a safe, reversible try-it-and-see:

| Try this | What you should see |
|---|---|
| Add a product with an empty name or SKU | Inline validation message; nothing saved |
| Create a product with SKU `DEMO-COFFEE` again | "SKU 'DEMO-COFFEE' already exists." |
| Adjust stock: remove more units than coffee has | Rejection — negative stock is never allowed (DEC-034) |
| Set coffee's exact stock to 0 | Status flips to **Out of Stock** (red) |
| Set coffee's stock back to 12 | Status returns to **Low Stock** |
| Deactivate a product with the confirm tick | It leaves the listings and cannot be selected for new sales; its history stays (DEC-048) |
| Re-upload `demo_sales_history.csv` | SHA-256 duplicate rejection (DEC-053) |
| Record a sale dated tomorrow | Rejected — future dates are refused (DEC-051) |

### Language

Switch the sidebar **Language** to العربية at any time: every page
flips to Arabic right-to-left, the status names, validation messages,
restocking explanations, and import messages appear in Arabic, while
SKUs, dates, DEC-xxx codes, and numerals stay Western. Switch back to
English just as easily.

---

## 6. Numbers in this guide

All counts and figures were measured on 2026-11-14 against the real
validator and the real services — none are invented. They anchor to
the dataset's last sale date (2026-11-13) and the recording dates in
step 4. As you record more sales, the app's figures legitimately drift
from this guide's snapshots; drift is the system working, not a bug.

## 7. Housekeeping

- **Regenerate the file:** `.venv/bin/python scripts/generate_demo_data.py`
  — the seed is fixed, so it always produces the same data.
- **Start over:** the import and everything you record lives in
  `data/smartstock.db` (git-ignored). Delete that file and the app
  recreates an empty database on next start. A prior database can be
  kept as a renamed copy, as was done for the manual-test data.
- The committed file is ~31 KB — small, seeded, and safe for version
  control; `tests/test_demo_data.py` re-validates it against the real
  validator so it can never silently break.
