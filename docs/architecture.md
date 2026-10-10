# Architecture — Month-End Variance Copilot

| | |
|---|---|
| Status | **Approved by PM, 10 Oct 2026** (WBS 1.2). C-001 and C-003 await sponsor sign-off (simulated) |
| Date | 10 October 2026 |
| Based on | Documents 01–08, version 1.0 |

Independent portfolio project. All data is synthetic and all stakeholders are assumed role personas. This is not a document of any real company and contains no internal or confidential information.

This document describes *how* the product is built. *What* it must do is defined in documents 04 (scope, business rules) and 05 (requirements). Where this document fills a gap in those documents, it references the open item (A-xx) in `docs/log_entries_for_07.md`. All A-xx items were approved by the PM on 10 Oct 2026 (D-014 to D-022, C-001 to C-004).

---

## 1. Design principles

| Principle | Why | Traces to |
|---|---|---|
| Numbers come only from the pipeline; the language model only writes words | Main control against invented figures | D-007, R01, FR-11, FR-12 |
| Transformations are SQL, mappings are tables | Logic can move to a data platform or KNIME | NFR-06, D-004, D-005, C4 |
| Every reported figure can be traced to a source file and line | Audit and internal control | NFR-03, S12 |
| Fail loudly on bad master data | A wrong mapping makes the consolidated numbers wrong | FR-04, R03 |
| Rebuild from scratch on every run | Identical results, no hidden state | NFR-02 |
| Works offline with no API key | Demo safety, no cost | NFR-05, R06 |
| Small modules, each explainable in two sentences | The PM must be able to explain all code | R04 |

## 2. System context

```
           ┌──────────────────────────── one laptop, no paid infrastructure ───────────────────────────┐
           │                                                                                            │
 CSV files │  data/raw/ ──► pipeline (Python + SQL on DuckDB) ──► analytics (pandas) ──► commentary  ──►│ Streamlit
 (synthetic)│  data/reference/                                                         │      ▲        │ dashboard
           │                                                                           │      │        │ (controller,
           │                                                       aggregated figures ▼      │ text    │  cost-centre
           │                                                              ┌────────────────────┐        │  owner)
           └──────────────────────────────────────────────────────────────│ LLM API (optional) │────────┘
                                                                          └────────────────────┘
```

No ERP, authentication or deployment (doc 04 §2). The only external call is the optional language-model API. Only rounded, aggregated figures for one flagged item are sent (NFR-04).

## 3. Layers and data flow

```
 ┌─ WBS 3.1 RAW ─────────────┐   ┌─ WBS 3.2 STAGING ─────────┐   ┌─ WBS 3.3 REPORTING ────┐
 │ raw_fab_north             │   │ stg_fab_north             │   │                        │
 │ raw_fab_alps              │──►│ stg_fab_alps   (common    │──►│ rpt_harmonised         │
 │ raw_fab_asia              │   │ stg_fab_asia    layout,   │   │  648 rows              │
 │ raw_wafer_volumes         │   │                 EUR,      │   │  (doc 04 §4.1)         │
 │ raw_fx_rates              │   │                 YYYY-MM)  │   │                        │
 │ ref_account_mapping       │   │ stg_wafer_volumes         │   └───────────┬────────────┘
 │ ref_cost_centre_mapping   │   │ dq_removed_duplicates     │               │
 │ ref_cost_behaviour        │   └───────────────────────────┘               │
 │ + source_file, source_line│                                               │
 └───────────────────────────┘     ┌─ WBS 3.4 QUALITY ──────────────────┐    │
                                   │ mapping gate (stop on unmapped)    │◄───┤
                                   │ dq_report, dq_reconciliation       │    │
                                   └────────────────────────────────────┘    │
 ┌─ WBS 4 ANALYTICS (pandas) ───────────────────────────────────────────┐    │
 │ an_variance  (flexed budget, volume and spend effect, spend_flag)    │◄───┘
 │ an_volume_flags (site × period)                                      │
 │ an_cost_per_wafer (site × period, plan and actual)                   │
 └──────────────────────────────┬───────────────────────────────────────┘
                                ▼
 ┌─ WBS 5 COMMENTARY ───────────────────────────────────────────────────┐
 │ context.py ─► llm.py ─► number_check.py ─► review.py                 │
 │  (rounded     (API or     (pass/fail;        (Draft / Approved,      │
 │   figures,     template)   retry once,        reviewer role, time,   │
 │   owner cause)             then template)     owner cause)           │
 │ every prompt, answer and check ─► logs/llm_log.jsonl                 │
 └──────────────────────────────┬───────────────────────────────────────┘
                                ▼
 ┌─ WBS 6 DASHBOARD (Streamlit + Plotly) ───────────────────────────────┐
 │ Overview · Site comparison · Variance waterfall · Flagged items with │
 │ commentary and approval · Data quality      "SYNTHETIC DATA" banner  │
 └──────────────────────────────────────────────────────────────────────┘
```

Table prefixes show which layer a table belongs to: `raw_`, `ref_`, `stg_`, `rpt_`, `dq_`, `an_`, `cm_`.

## 4. Storage

| Store | Content | Lifetime |
|---|---|---|
| `data/warehouse/variance.duckdb` | All raw, staging, reporting, quality and analytics tables | **Deleted and rebuilt on every run** (NFR-02). Not committed. |
| `data/review/review.duckdb` | `cm_commentary` (drafts, status, reviewer role, approved_at), `cm_owner_cause` | **Kept between runs**, so approvals and causes survive a rebuild. Not committed. (A-18) |
| `logs/llm_log.jsonl` | One JSON line per prompt, answer and number-check result | Append-only. Not committed. (A-10) |
| `config.yaml` | Materiality thresholds, rounding, language, LLM settings (no secrets) | Committed. (A-08) |
| `.env` | LLM API key | Never committed. |

**Why two databases:** the pipeline must give identical results on every run, so the warehouse is rebuilt from nothing. Approvals are human decisions and must not be lost on a rebuild. Commentary rows are keyed by site, period, area and account, so they reattach to the rebuilt variance table.

## 5. Data model

### 5.1 Raw (WBS 3.1)
Every source column is loaded as text, unchanged, plus:
- `source_file`: the file name;
- `source_line`: the physical line in the file, with the header as line 1 (A-11).

Values are typed in staging, not here, so the raw layer is a faithful copy of the file.

### 5.2 Staging (WBS 3.2): common layout for each site

| Column | Type | Notes |
|---|---|---|
| site | text | `FAB_NORTH`, `FAB_ALPS`, `FAB_ASIA` |
| period | text | `YYYY-MM` (FR-02) |
| local_cost_centre | text | |
| local_account_code | text | Text type, because FAB_ASIA codes are alphanumeric |
| plan_eur | decimal(18,2) | FR-03 |
| actual_eur | decimal(18,2), nullable | NULL means "actual not posted" |
| source_file | text | |
| source_line_plan | int | (A-01) |
| source_line_actual | int | Same as plan for NORTH and ALPS; the separate ACT line for ASIA |

Site-specific steps:
- **FAB_NORTH:** convert types only.
- **FAB_ALPS:**
  - convert `01.2026` to `2026-01`;
  - replace the decimal comma;
  - multiply by 1,000 (TEUR to EUR);
  - an empty `Ist_TEUR` becomes NULL.
- **FAB_ASIA:**
  - convert `Jan-26` to `2026-01`;
  - remove exact duplicates (with `ROW_NUMBER()` over all source columns; removed lines go to `dq_removed_duplicates`);
  - pivot the BUD and ACT rows into plan and actual;
  - divide MYR by `myr_per_eur` for the month.

### 5.3 Reporting (WBS 3.3): `rpt_harmonised`
Doc 04 §4.1 columns, with `source_row` split into `source_line_plan` and `source_line_actual` (A-01, needs a change entry). The table is `UNION ALL` of the three staging tables, joined to both mapping tables. Grain: site × period × group_area × group_account, so 648 rows, with a uniqueness test.

### 5.4 Quality (WBS 3.4)

| Table | Content |
|---|---|
| `dq_report` | One row per finding: type (`duplicate_removed`, `actual_not_posted`), site, period, local codes, source line, amount |
| `dq_reconciliation` | Per site × period × measure (plan, actual): source_total_eur, harmonised_total_eur, corrections_eur, difference, difference_pct, pass (A-02, A-03) |

The **mapping gate** runs before `rpt_harmonised` is built. It anti-joins staging against both mapping tables. If anything is unmapped, the run stops with **one** error that lists every unmapped code (A-12).

### 5.5 Analytics (WBS 4)

| Table | Grain | Key columns |
|---|---|---|
| `an_variance` | Same as rpt_harmonised | variable_share, volume_ratio, flexed_eur, total_var, volume_effect, spend_effect, spend_flag, actual_posted |
| `an_volume_flags` | site × period | plan_wafers, actual_wafers, volume_ratio, volume_flag |
| `an_cost_per_wafer` | site × period | cpw_plan, cpw_actual, complete (false if any actual is missing) |

For the row with a missing actual: total_var, spend_effect and spend_flag are NULL; volume_effect is still calculated (C-003).

## 6. Commentary design (WBS 5)

1. **context.py** builds one context per flagged item: the rounded figures only (EUR thousands, percentages to one decimal) plus the owner's cause, if any. That context is the *complete set of numbers allowed* in the text.
2. **llm.py** sends the context and a fixed prompt to the provider named in `LLM_PROVIDER` / `LLM_MODEL` (env vars). With no key, or on error or timeout (20 s, R06), it uses a template that fills in the same context.
3. **number_check.py** extracts every number in the draft, ignores period labels, and compares the rest with the context. Fail → regenerate once → fail again → template.
4. **review.py** stores the draft as `Draft`. It allows edits; an edited text is re-checked before approval. It records `Approved` with reviewer role and timestamp, and stores owner causes.
5. Every step writes to `logs/llm_log.jsonl` (NFR-04).

The number check also runs on template output and on human edits, so no unchecked figure can reach an `Approved` text.

## 7. Configuration (`config.yaml`, A-08)

```yaml
materiality:
  spend_abs_eur: 50000
  spend_pct: 0.05
  volume_pct: 0.05
reconciliation_tolerance_pct: 0.0001   # 0.01 %
commentary:
  language: en          # de = FR-16 (Could)
  llm_timeout_s: 20
  max_regenerations: 1
```

## 8. Execution

| Command | Does |
|---|---|
| `python src/generate_data.py` | Writes `data/raw/` and `fx_rates.csv` (exists; not changed) |
| `python -m src.pipeline.run` | Deletes the warehouse, then runs ingest → staging → mapping gate → reporting → quality → analytics. Prints run time (SC-6, < 2 min) |
| `python -m src.commentary.run` (name to confirm in WP 5) | Drafts commentary for the flagged items |
| `streamlit run app/dashboard.py` | Dashboard |
| `pytest` | All tests (SC-7) |

## 9. Testing strategy

| Level | Example | Requirement |
|---|---|---|
| Ingest | Raw row counts 216 / 216 / 433 / 27 / 9 | FR-01 |
| Transformation | 9 periods per site; local codes never empty; source lines never empty | FR-02, FR-05, NFR-03 |
| Mapping | A fixture with an unknown code makes the run fail | FR-04 |
| Quality | Exactly 1 duplicate and 1 missing actual; reconciliation passes | FR-06, SC-2, SC-3 |
| Variance | volume + spend = total on every posted row; exactly 3 + 3 flags | FR-07–09, SC-4 |
| Commentary | Invented number fails, correct draft passes, no-key run passes | FR-12, NFR-05, SC-5 |
| End to end | Two runs give identical tables | NFR-02 |

Tests use the real generated data for the planted-event assertions, and small in-memory fixtures for the error paths.

## 10. Repository layout

As doc 04 §7, plus the additions marked ★ (to be approved through doc 07):

```
docs/                 documents 01–08 (.docx), md/, architecture.md ★, log_entries_for_07.md ★
data/raw/             generated input (committed so the repo works without running the generator)
data/reference/       mapping and behaviour tables (committed)
data/warehouse/       rebuilt DuckDB (ignored)
data/review/  ★       approvals and owner causes (ignored)
src/generate_data.py  exists, do not change
src/pipeline/         ingest.py, quality.py, run.py, sql/
src/analytics/        variance.py
src/commentary/       context.py, llm.py, number_check.py, review.py
app/dashboard.py
tests/
knime/
logs/  ★              LLM log (ignored)
config.yaml  ★
README.md, requirements.txt, CLAUDE.md ★
```
