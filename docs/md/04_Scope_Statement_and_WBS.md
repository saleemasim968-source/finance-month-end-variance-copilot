Month-End Variance Copilot

**Scope Statement and WBS**

| Document ID | VC-04 |
|---|---|
| Process group | Planning |
| Version | 1.0 (baseline) |
| Date | 10 October 2026 |
| Project manager | Asim |
| Sponsor | Head of Frontend Cluster Finance (persona S01) |

Independent portfolio project. All data is synthetic and all stakeholders are assumed role personas. This is not a document of any real company and contains no internal or confidential information.

## 1. Product scope description

The product is a local prototype that turns three differently formatted site cost reports into one reviewed variance report. It has five parts that run in sequence.

- **Ingest:** load the raw site files and reference tables into a database without manual editing.

- **Harmonise:** convert every site to the same periods, currency, units, accounts and cost areas.

- **Check:** find duplicates, missing values and unmapped codes, and reconcile against source totals.

- **Analyse:** calculate variances, split them into a volume effect and a spend effect, and flag material ones.

- **Explain:** draft commentary for flagged items, verify every figure, and record controller approval.

A dashboard presents the results.

## 2. Scope boundaries

| In scope | Out of scope |
|---|---|
| Three fictional sites, nine months of 2026 | Real company data, names or systems |
| Cost types: personnel, depreciation, energy, materials, maintenance, external services | Revenue, margin, balance sheet, accruals, intercompany |
| Plan versus actual comparison | Forecasting and prior-year comparison |
| File-based input | ERP or data-platform interfaces |
| Maintained mapping tables | AI-suggested account mapping (noted as a follow-up idea) |
| Commentary in English; German as an option | Other languages |
| Local dashboard for one user | User accounts, roles and deployment |
| Cost-centre level data | Any person-level data |

## 3. Input data specification

The synthetic data is produced by src/generate_data.py, which already exists. It writes the following files. Each site file is different on purpose.

| File | Layout |
|---|---|
| data/raw/fab_north_costs.csv | Comma-separated. Columns: period (2026-01), cost_center, account_code, account_name, plan, actual. Amounts in EUR. 216 rows. |
| data/raw/fab_alps_kosten.csv | Semicolon-separated with decimal comma. Columns: Periode (01.2026), Kostenstelle, Kontonummer, Kontobezeichnung, Plan_TEUR, Ist_TEUR. Amounts in thousands of EUR. 216 rows. One actual value is empty. |
| data/raw/fab_asia_gl_export.csv | Comma-separated. Columns: Period (Jan-26), CC, GL Account, GL Description, Version (BUD or ACT), Amount (MYR). Plan and actual are separate rows. Amounts in Malaysian ringgit. 433 rows, including one duplicate line. |
| data/raw/wafer_volumes.csv | Columns: site, period, plan_wafers, actual_wafers. 27 rows. |
| data/reference/fx_rates.csv | Columns: period, myr_per_eur. 9 rows. EUR amount = MYR amount divided by myr_per_eur. |

### 3.1 Reference tables to be created in work package 2.2

| File | Content |
|---|---|
| data/reference/account_mapping.csv | site, local_account_code, local_account_name, group_account |
| data/reference/cost_centre_mapping.csv | site, local_cost_centre, group_area |
| data/reference/cost_behaviour.csv | group_account, variable_share |

### 3.2 Account mapping

| Group account | FAB_NORTH | FAB_ALPS | FAB_ASIA | Variable share |
|---|---|---|---|---|
| Personnel | 400000 | 6000 | P100 | 0.0 |
| Depreciation | 410000 | 6100 | D200 | 0.0 |
| Energy | 420000 | 6200 | U300 | 0.3 |
| Materials | 430000 | 6300 | M400 | 0.9 |
| Maintenance | 440000 | 6400 | R500 | 0.2 |
| External services | 450000 | 6500 | S600 | 0.0 |

The variable share is the part of an account that moves with wafer volume. It is an assumption of this project and is kept in a table so it can be changed.

### 3.3 Cost-centre mapping

| Group area | FAB_NORTH | FAB_ALPS | FAB_ASIA |
|---|---|---|---|
| Lithography | CC1010 | KST-210 | MY-LIT |
| Etch | CC1020 | KST-220 | MY-ETC |
| Diffusion | CC1030 | KST-230 | MY-DIF |
| Facilities | CC1900 | KST-900 | MY-FAC |

## 4. Business rules

### 4.1 Harmonised reporting table

One row per site, period, group area and group account, with these columns: site, period (YYYY-MM), group_area, group_account, local_cost_centre, local_account_code, plan_eur, actual_eur, source_file, source_row.

### 4.2 Data-quality rules

| Rule | Treatment |
|---|---|
| Exact duplicate line in a source file | Keep one, remove the others, log each removal with file and row |
| Missing actual value | Keep the row, mark it "actual not posted", exclude it from variance flags, list it in the report |
| Local account or cost centre without a mapping | Stop the run with a clear error |
| Reconciliation | Per site and period: source total in EUR must equal harmonised total plus logged corrections, within 0.01% |

### 4.3 Variance method

Sign convention: a positive variance means cost above plan and is unfavourable.

| Measure | Formula |
|---|---|
| Volume ratio | actual_wafers / plan_wafers, per site and period |
| Flexed budget | plan_eur x ((1 - variable_share) + variable_share x volume ratio) |
| Total variance | actual_eur - plan_eur |
| Volume effect | flexed budget - plan_eur |
| Spend effect | actual_eur - flexed budget |
| Check | volume effect + spend effect = total variance |
| Cost per wafer, actual | sum of actual_eur / actual_wafers, per site and period |
| Cost per wafer, plan | sum of plan_eur / plan_wafers, per site and period |

### 4.4 Materiality flags

- **Spend flag:** a row is flagged when the absolute spend effect is at least EUR 50,000 and at least 5% of the flexed budget.

- **Volume flag:** a site and period is flagged when actual wafers differ from plan by at least 5%.

- Both thresholds are configuration values.

### 4.5 Commentary rules

- Commentary is drafted only for flagged items.

- The model receives only the calculated figures for that item, plus the cause entered by the cost-centre owner if one exists.

- Amounts are given to the model already rounded: EUR in thousands, percentages with one decimal.

- The number check extracts every number from the draft. Each must match a value in the context given to the model. Period labels are excluded.

- A draft that fails is regenerated once. If it fails again, the template commentary is used.

- Every commentary has a status of "Draft" or "Approved", with the reviewer role and time of approval.

- Prompts, answers and check results are logged.

## 5. Events planted in the synthetic data

These are used to test whether the solution finds what it should. They correspond to success criteria SC-3 and SC-4.

| Type | Where | What |
|---|---|---|
| Business event | FAB_NORTH, May, Maintenance, Lithography | About EUR 480,000 of unplanned cost (tool-down) |
| Business event | FAB_ALPS, July and August, Energy | About 22% above expected cost in all areas (price spike) |
| Business event | FAB_ASIA, July to September | Wafer volume about 14% below plan (weak loading) |
| Data issue | FAB_ALPS, September, KST-220, account 6500 | Actual value missing |
| Data issue | FAB_ASIA, June, MY-ETC, account M400, version ACT | Line exported twice |

With the thresholds in section 4.4, the expected result on this data set is exactly three spend flags (the tool-down row, and Energy in Facilities at FAB_ALPS in July and in August) and exactly three volume flags (FAB_ASIA in July, August and September). Automated tests should assert this.

## 6. Work breakdown structure

| WBS | Work package | Result |
|---|---|---|
| 1 | Project management |  |
| 1.1 | Initiating | Charter, stakeholder register |
| 1.2 | Planning | Management plan, scope statement, traceability matrix, risk register |
| 1.3 | Monitoring and controlling | Status entries, decision and change log |
| 1.4 | Closing | Closing report with lessons learned |
| 2 | Data foundation |  |
| 2.1 | Synthetic data generator | Raw site files, volumes, FX rates (complete) |
| 2.2 | Reference tables | Account mapping, cost-centre mapping, cost behaviour |
| 3 | ELT pipeline |  |
| 3.1 | Raw load | Raw tables in DuckDB, unchanged, with file name and row number |
| 3.2 | Staging per site | One cleaned table per site in a common layout |
| 3.3 | Harmonised reporting table | Table as defined in section 4.1 |
| 3.4 | Data-quality checks and reconciliation | Data-quality report, reconciliation table |
| 4 | Variance analytics |  |
| 4.1 | Variance calculation and decomposition | Variance table with volume and spend effects |
| 4.2 | Materiality flags | List of flagged items |
| 4.3 | Cost per wafer | Table by site and period |
| 5 | AI commentary |  |
| 5.1 | Context builder and prompt | Rounded figures per flagged item |
| 5.2 | Model client and template fallback | Draft commentary with or without an API key |
| 5.3 | Number check | Pass or fail per draft, logged |
| 5.4 | Review workflow | Status, reviewer, owner cause input |
| 6 | Dashboard | Overview, site comparison, variance waterfall, flagged items with commentary, data quality |
| 7 | Validation and transfer |  |
| 7.1 | Automated tests | Test suite, all passing |
| 7.2 | KNIME rebuild of the harmonisation step | Workflow file and screenshot |
| 7.3 | README and demo script | Setup guide, three-minute demo |
| 7.4 | Business case | One page: process before and after, estimated time saving, assumptions |

## 7. Repository structure

| Path | Content |
|---|---|
| docs/ | Project documents 01 to 08 |
| data/raw/, data/reference/ | Input files and reference tables |
| data/warehouse/ | DuckDB database file (not committed) |
| src/generate_data.py | Synthetic data generator (exists) |
| src/pipeline/ | ingest.py, quality.py, run.py and a sql/ folder with staging and reporting queries |
| src/analytics/variance.py | Variance calculation, flags, cost per wafer |
| src/commentary/ | context.py, llm.py, number_check.py, review.py |
| app/dashboard.py | Streamlit dashboard |
| tests/ | pytest tests |
| knime/ | KNIME workflow export |
| README.md, requirements.txt | Setup and pinned packages |

## 8. Acceptance criteria

The product is accepted when every "Must" requirement in document 05 has the status "Verified" and success criteria SC-1 to SC-8 in the charter are met.
