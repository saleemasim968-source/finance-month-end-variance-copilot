# Month-End Variance Copilot — CLAUDE.md

Weekend portfolio project (10–11 Oct 2026). The specification is the eight documents in `docs/` (Word originals) and `docs/md/` (markdown conversions). **The documents are the source of truth; this file is a summary.** If they disagree with this file, the documents win. Raise the conflict; don't resolve it silently.

All data is synthetic, and every site and stakeholder is fictional. No real company names, figures or person-level data may ever enter the repo (NFR-01, R05).

## Working rules (from the project manager)

1. Build **one WBS work package at a time**, then **stop for review**. Never start the next package unprompted.
2. After each package:
   - explain every new file in plain language (R04: each module explainable in two sentences);
   - run the quality gate for that package (doc 03 §7, table below);
   - report which requirement IDs (doc 05) are now **Verified**, and which are only **Built**.
3. **`src/generate_data.py` must not be modified.** It was written in WP 2 with the PM's permission (D-023) and is now frozen. `tests/test_data_foundation.py` checks that the committed data matches a fresh run.
4. Record every decision, deviation, issue or change in `docs/log_entries_for_07.md`, ready to copy into doc 07 (D-xxx decisions, C-xxx changes, I-xxx issues).
5. "Must" requirements and success criteria can only be changed with sponsor approval via doc 07. The PM may drop "Should" and "Could" items.
6. Do not write product code for a package before it is the current package.

## Scope (doc 01, doc 04)

The tool takes three differently formatted site cost reports (FAB_NORTH, FAB_ALPS, FAB_ASIA; Jan–Sep 2026) and:
**Ingest → Harmonise → Check → Analyse → Explain**, then shows the results on a dashboard.

- In scope: plan vs actual for six cost types, file-based input, maintained mapping tables, AI commentary (English, German optional), and a local single-user dashboard.
- Out of scope: real data, ERP or platform interfaces, auth and deployment, forecasting, prior year, revenue, balance sheet, accruals, intercompany, AI-suggested mapping, and person-level data.

## Architecture

Full design, including table schemas, storage and commentary controls: `docs/architecture.md`. Summary:

```
data/raw/*.csv ─┐
data/reference/ ┴─> [3.1 raw load] ─> raw_* tables (unchanged + source_file, source_row)
                     │                (DuckDB file: data/warehouse/, not committed)
                     v
                [3.2 staging, SQL] ─> stg_fab_north / stg_fab_alps / stg_fab_asia
                     │   common layout, period YYYY-MM, amounts in EUR
                     v
                [3.3 reporting, SQL] ─> rpt_harmonised (doc 04 §4.1)
                     │   joins account_mapping + cost_centre_mapping; unmapped => hard stop
                     v
                [3.4 quality.py] ─> dq_report, reconciliation
                     v
                [4 analytics/variance.py, pandas] ─> variance table, flags, cost per wafer
                     v
                [5 commentary/] context.py -> llm.py (API or template) -> number_check.py -> review.py
                     v                                     (all prompts, answers, checks logged)
                [6 app/backend (FastAPI API) + app/frontend (HTML, Plotly.js), C-005]
```

Orchestrated by `src/pipeline/run.py`: one command, empty DB to results in under 2 minutes, deterministic (NFR-02).

Stack (doc 03 §10): Python ≥ 3.11, DuckDB, SQL transformations, pandas, FastAPI + HTML/Plotly.js frontend (C-005 replaces Streamlit), pytest, KNIME (harmonisation rebuild). The LLM provider and model are set through env vars, and a template fallback runs without a key. LLM spend cap: EUR 5.

## Repository structure (doc 04 §7)

| Path | Content |
|---|---|
| `docs/` | Docs 01–08 (.docx), `docs/md/` conversions, `log_entries_for_07.md` |
| `data/raw/`, `data/reference/` | Input files and reference tables |
| `data/warehouse/` | DuckDB file (gitignored) |
| `src/generate_data.py` | Synthetic data generator (**exists, do not change**) |
| `src/pipeline/` | `ingest.py`, `quality.py`, `run.py`, `sql/` (staging + reporting) |
| `src/analytics/variance.py` | Variance, flags, cost per wafer |
| `src/commentary/` | `context.py`, `llm.py`, `number_check.py`, `review.py` |
| `app/backend/`, `app/frontend/` | Backend API and web frontend (C-005) |
| `tests/` | pytest |
| `knime/` | KNIME workflow export |
| `README.md`, `requirements.txt` | Setup, pinned packages |

## Input data (doc 04 §3)

| File | Format | Rows |
|---|---|---|
| `data/raw/fab_north_costs.csv` | `,`; period `2026-01`; cost_center, account_code, account_name, plan, actual; EUR | 216 |
| `data/raw/fab_alps_kosten.csv` | `;` with decimal comma; Periode `01.2026`; Kostenstelle, Kontonummer, Kontobezeichnung, Plan_TEUR, Ist_TEUR; **TEUR** | 216 (1 empty actual) |
| `data/raw/fab_asia_gl_export.csv` | `,`; Period `Jan-26`; CC, GL Account, GL Description, Version (BUD/ACT), Amount (MYR); **long format** | 433 (1 duplicate) |
| `data/raw/wafer_volumes.csv` | site, period, plan_wafers, actual_wafers | 27 |
| `data/reference/fx_rates.csv` | period, myr_per_eur. **EUR = MYR / myr_per_eur** | 9 |

## Reference tables (WP 2.2, doc 04 §3.1–3.3)

- `account_mapping.csv`: site, local_account_code, local_account_name, group_account
- `cost_centre_mapping.csv`: site, local_cost_centre, group_area
- `cost_behaviour.csv`: group_account, variable_share

| Group account | NORTH | ALPS | ASIA | variable_share |
|---|---|---|---|---|
| Personnel | 400000 | 6000 | P100 | 0.0 |
| Depreciation | 410000 | 6100 | D200 | 0.0 |
| Energy | 420000 | 6200 | U300 | 0.3 |
| Materials | 430000 | 6300 | M400 | 0.9 |
| Maintenance | 440000 | 6400 | R500 | 0.2 |
| External services | 450000 | 6500 | S600 | 0.0 |

| Group area | NORTH | ALPS | ASIA |
|---|---|---|---|
| Lithography | CC1010 | KST-210 | MY-LIT |
| Etch | CC1020 | KST-220 | MY-ETC |
| Diffusion | CC1030 | KST-230 | MY-DIF |
| Facilities | CC1900 | KST-900 | MY-FAC |

## Business rules (doc 04 §4)

**Harmonised table:** one row per site × period × group_area × group_account (3×9×4×6 = 648 rows). Columns: site, period, group_area, group_account, local_cost_centre, local_account_code, plan_eur, actual_eur, source_file, source_row.

**Data quality:**
- Exact duplicate: keep one copy, remove the rest, and log each removal (file + row).
- Missing actual: keep the row, mark it "actual not posted", exclude it from flags, and list it in the report.
- Unmapped account or cost centre: **stop the run** with a clear error.
- Reconciliation: per site and period, source EUR total = harmonised total + logged corrections, within 0.01%.

**Variance** (positive = cost above plan = unfavourable):
- volume_ratio = actual_wafers / plan_wafers (per site and period)
- flexed = plan_eur × ((1 − variable_share) + variable_share × volume_ratio)
- total = actual − plan; volume_effect = flexed − plan; spend_effect = actual − flexed
- invariant: volume_effect + spend_effect = total
- cost per wafer = Σ eur / wafers, for plan and actual, per site and period

**Flags** (thresholds are config values):
- Spend flag (row level): |spend_effect| ≥ EUR 50,000 **and** ≥ 5% of flexed.
- Volume flag (site × period): |actual − plan wafers| / plan ≥ 5%.

**Expected on this data:** exactly 3 spend flags (NORTH May Maintenance/Lithography; ALPS Jul and Aug Energy/Facilities) and exactly 3 volume flags (ASIA Jul, Aug, Sep). Tests must assert this.

**Commentary:**
- Drafted for flagged items only, from calculated figures plus the owner's cause (if any).
- Figures are pre-rounded: EUR in thousands, percentages to 1 decimal.
- Number check: every number in the draft must appear in the context; period labels are exempt.
- On failure: regenerate once, then fall back to the template.
- Status is Draft or Approved, with reviewer role and timestamp. Every prompt, answer and check is logged.

## Planted events (doc 04 §5)

| Type | Where | What |
|---|---|---|
| Business | NORTH, May, Maintenance, Lithography | ~EUR 480k tool-down |
| Business | ALPS, Jul + Aug, Energy, all areas | ~22% price spike |
| Business | ASIA, Jul–Sep | volume ~14% below plan |
| Data | ALPS, Sep, KST-220, 6500 | actual missing |
| Data | ASIA, Jun, MY-ETC, M400, ACT | line exported twice |

## Quality gates (doc 03 §7)

| WBS | Gate |
|---|---|
| 2 | Data files exist with the specified row counts; reference tables cover every local code |
| 3 | Source totals = harmonised + logged corrections per site and period; both planted data issues reported |
| 4 | volume + spend = total on every row; the 3 planted events are flagged |
| 5 | No figure in any released commentary is missing from the model context (number-check log) |
| 6 | Every dashboard figure equals the variance table (spot-check 5 values) |
| 7 | All tests pass; a clean run from an empty DB works with one command |

## Requirement IDs (doc 05) — 21 Must / 3 Should / 1 Could

| ID | Short | Pri | WBS |
|---|---|---|---|
| BR-01 | Business case: before/after + time saving | Must | 7.4 |
| FR-01 | Load all files without manual edits (row counts) | Must | 3.1 |
| FR-02 | Periods → YYYY-MM (9 per site) | Must | 3.2 |
| FR-03 | Amounts → EUR (TEUR ×1000; MYR / rate) | Must | 3.2 |
| FR-04 | Map via tables; unmapped stops run | Must | 2.2, 3.3 |
| FR-05 | Keep local codes on every row | Must | 3.3 |
| FR-06 | Detect duplicates, missing actuals, unmapped; reconcile | Must | 3.4 |
| FR-07 | Variance per site/period/area/account | Must | 4.1 |
| FR-08 | Volume and spend split via flexed budget | Must | 4.1 |
| FR-09 | Configurable flags; exactly 3 + 3 | Must | 4.2 |
| FR-10 | Cost per wafer | Should | 4.3 |
| FR-11 | Commentary from calculated figures only | Must | 5.1, 5.2 |
| FR-12 | Number check rejects invented figures | Must | 5.3 |
| FR-13 | Draft/Approved status, reviewer, time; edit before approval | Must | 5.4 |
| FR-14 | Owner cause input used in commentary | Should | 5.4 |
| FR-15 | Dashboard (overview, site comparison, waterfall, flagged + commentary, DQ) | Must | 6 |
| FR-16 | German commentary | Could | 5.2 |
| NFR-01 | Synthetic only; no person-level data | Must | 2 |
| NFR-02 | One command, < 2 min, deterministic | Must | 3, 7.1 |
| NFR-03 | source_file + source_row on every row | Must | 3.1, 3.3 |
| NFR-04 | Only aggregates to LLM; log prompts, answers, checks | Must | 5.1, 5.3 |
| NFR-05 | Works without an LLM key (template) | Must | 5.2 |
| NFR-06 | SQL transformations; mappings as tables; KNIME parity | Should | 3, 7.2 |
| NFR-07 | Automated tests for transform and variance logic | Must | 7.1 |
| NFR-08 | "Synthetic / independent" notice on every screen and document | Must | 6, 7.3 |

Status values: Open → Built → Verified (or Removed via doc 07).

## Success criteria (doc 01 §4)

SC-1 100% rows mapped · SC-2 reconciliation < 0.01% · SC-3 2/2 data issues found · SC-4 3/3 events flagged · SC-5 100% commentary figures traceable · SC-6 one command < 2 min · SC-7 all tests pass · SC-8 one-page business case.

## Open questions

The design decisions D-009 to D-022 and changes C-001 to C-004 in `docs/log_entries_for_07.md` are approved and override doc 04 where they differ (e.g. `source_line_plan`/`source_line_actual` instead of `source_row`). Only I-001 (missing generator) is still open. Don't guess an answer to any item marked OPEN.

## Commands

- Set up: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Regenerate data: `.venv/bin/python src/generate_data.py`. The output must equal the committed files; a test checks this.
- Tests (quality gates): `.venv/bin/python -m pytest -v`
- Run the pipeline: `.venv/bin/python -m src.pipeline.run` (rebuilds `data/warehouse/variance.duckdb`, drafts commentary for new flagged items)
- Start the app: `.venv/bin/python -m app.backend` → http://127.0.0.1:8000
- Redraft commentary: `.venv/bin/python -m src.commentary.run --regenerate [--language de]`
- KNIME parity: `.venv/bin/python knime/check_parity.py`
