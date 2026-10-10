# KNIME rebuild of the harmonisation step (WBS 7.2, NFR-06)

> Independent portfolio project. All data is synthetic.

**Purpose.** Show that the harmonisation logic is not locked into Python: the same result can be built in a low-code tool that finance teams already use (stakeholder S10, conflict C4). The KNIME workflow reads the three raw site files and the mapping tables and produces the same totals as the SQL pipeline.

**Status.** KNIME is not installed on the build machine, so the workflow file has not been created yet. This guide describes it node by node, and `check_parity.py` verifies the result automatically. Build time is about 45 minutes in KNIME Analytics Platform 5.x. When it passes, export the workflow to `knime/harmonisation.knwf`, add a screenshot as `knime/workflow.png`, and set NFR-06 to Verified (doc 05).

## Inputs

| File | Settings in the CSV Reader |
|---|---|
| `data/raw/fab_north_costs.csv` | delimiter `,`; all columns as String |
| `data/raw/fab_alps_kosten.csv` | delimiter `;`; encoding UTF-8; all columns as String |
| `data/raw/fab_asia_gl_export.csv` | delimiter `,`; all columns as String |
| `data/reference/fx_rates.csv` | delimiter `,` |
| `data/reference/account_mapping.csv`, `cost_centre_mapping.csv` | delimiter `,`; code columns as String |

Read everything as String first, to mirror the raw layer. Convert in the steps below.

## Workflow, one branch per site

**FAB_NORTH** (EUR, period already `YYYY-MM`)
1. *CSV Reader*, then *Duplicate Row Filter* (all columns; keep the first occurrence).
2. *String to Number* on `plan`, `actual` (decimal separator `.`).
3. *Column Rename*: `cost_center` → `local_cost_centre`, `account_code` → `local_account_code`, `plan` → `plan_eur`, `actual` → `actual_eur`.
4. *Constant Value Column*: `site` = `FAB_NORTH`.

**FAB_ALPS** (thousands of EUR, decimal comma, period `MM.YYYY`)
1. *CSV Reader*, then *Duplicate Row Filter*.
2. *String Manipulation*: `period` = `join(substr($Periode$, 3, 4), "-", substr($Periode$, 0, 2))`.
3. *String Manipulation* twice: replace `,` with `.` in `Plan_TEUR` and `Ist_TEUR`.
4. *String to Number* on both. An empty `Ist_TEUR` must stay missing, not 0.
5. *Math Formula*: `plan_eur` = `round($Plan_TEUR$ * 1000, 2)`; `actual_eur` = `round($Ist_TEUR$ * 1000, 2)`.
6. Rename `Kostenstelle` → `local_cost_centre` and `Kontonummer` → `local_account_code`; add `site` = `FAB_ALPS`.

**FAB_ASIA** (MYR, period `Mon-YY`, plan and actual on separate rows, one duplicate line)
1. *CSV Reader*, then *Duplicate Row Filter* (all columns). This removes the planted duplicate (June, MY-ETC, M400, ACT).
2. *Rule Engine* or *String Manipulation* to map `Jan-26` … `Sep-26` to `2026-01` … `2026-09`.
3. *Joiner* with `fx_rates.csv` on `period`.
4. *Math Formula*: `amount_eur` = `round($Amount$ / $myr_per_eur$, 2)`. **Round each line to cents before pivoting**, as the SQL does (D-029), or totals can differ by a few cents.
5. *Pivot*: group by `period`, `CC`, `GL Account`; pivot on `Version`; aggregate `amount_eur` with Sum. Rename `BUD` → `plan_eur` and `ACT` → `actual_eur`.
6. Rename `CC` → `local_cost_centre` and `GL Account` → `local_account_code`; add `site` = `FAB_ASIA`.

## Harmonise and total

1. *Concatenate* the three branches, keeping the columns `site`, `period`, `local_cost_centre`, `local_account_code`, `plan_eur`, `actual_eur`.
2. *Joiner* (inner) with `cost_centre_mapping.csv` on `site` + `local_cost_centre`, then with `account_mapping.csv` on `site` + `local_account_code`. Check that the row count stays at **648**. A lower count means an unmapped code, which the SQL pipeline would stop on.
3. *GroupBy* `site`, `period`: Count → `rows`; Sum `plan_eur`; Sum `actual_eur` (missing values ignored).
4. *CSV Writer* to `knime/output/harmonised_totals_knime.csv` with the columns `site,period,rows,plan_eur,actual_eur`.

## Verify

```bash
python knime/check_parity.py
```

The check passes when all 27 site-periods match `knime/expected_harmonised_totals.csv` (same row count, totals within EUR 0.01). The expected file comes from the SQL pipeline. After any data change, rerun the pipeline and refresh it with:

```bash
python -m src.pipeline.run
python knime/check_parity.py --export-expected
```
