Month-End Variance Copilot

**Requirements Traceability Matrix**

| Document ID | VC-05 |
|---|---|
| Process group | Planning; Monitoring and Controlling |
| Version | 1.0 (baseline) |
| Date | 10 October 2026 |
| Project manager | Asim |
| Sponsor | Head of Frontend Cluster Finance (persona S01) |

Independent portfolio project. All data is synthetic and all stakeholders are assumed role personas. This is not a document of any real company and contains no internal or confidential information.

## 1. Purpose

This matrix lists every requirement and links it to its source, its work package, the planned code location and the way it is verified. It is the scope baseline for the build and the checklist for acceptance. Stakeholder IDs refer to document 02. WBS codes refer to document 04.

## 2. Requirements traceability matrix

| ID | Requirement | Source | Priority | WBS | Planned location | Verification | Status |
|---|---|---|---|---|---|---|---|
| BR-01 | Document the month-end process before and after, with an estimated time saving and its assumptions | S01, S02 | Must | 7.4 | docs/business_case | Review against SC-8 | Open |
| FR-01 | Load all three site files and the volume and FX files without manual editing | S04, S09 | Must | 3.1 | src/pipeline/ingest.py | Test: row counts per raw table equal file row counts | Open |
| FR-02 | Convert all period formats to YYYY-MM | S05 | Must | 3.2 | src/pipeline/sql/ | Test: nine distinct periods per site | Open |
| FR-03 | Convert all amounts to EUR (thousands scaling for FAB_ALPS, monthly FX rate for FAB_ASIA) | S05 | Must | 3.2 | src/pipeline/sql/ | Test: reconciliation within 0.01% (SC-2) | Open |
| FR-04 | Map local accounts and cost centres to the group structure through maintained mapping tables; unmapped codes stop the run | S05, S10 | Must | 2.2, 3.3 | data/reference/, src/pipeline/sql/ | Test: 100% rows mapped (SC-1); test with an unknown code fails | Open |
| FR-05 | Keep the local account and cost-centre codes on every harmonised row | S03 | Must | 3.3 | src/pipeline/sql/ | Test: local code columns are never empty | Open |
| FR-06 | Detect and report duplicates, missing actuals and unmapped codes, and reconcile against source totals | S06, S12 | Must | 3.4 | src/pipeline/quality.py | Test: exactly one duplicate and one missing actual reported (SC-3) | Open |
| FR-07 | Calculate plan-versus-actual variance per site, period, area and account | S04, S05 | Must | 4.1 | src/analytics/variance.py | Test: total variance = actual - plan | Open |
| FR-08 | Split each variance into a volume effect and a spend effect using a flexed budget | S05, S01 | Must | 4.1 | src/analytics/variance.py | Test: volume effect + spend effect = total variance on every row | Open |
| FR-09 | Flag material variances using configurable thresholds | S01, S04 | Must | 4.2 | src/analytics/variance.py | Test: exactly three spend flags and three volume flags (SC-4) | Open |
| FR-10 | Show plan and actual cost per wafer by site and period | S01 | Should | 4.3 | src/analytics/variance.py | Test: value equals total cost divided by wafers | Open |
| FR-11 | Draft commentary for each flagged item from calculated figures only | S04, S01 | Must | 5.1, 5.2 | src/commentary/context.py, llm.py | Review of drafts for all flagged items | Open |
| FR-12 | Reject any draft that contains a figure not present in the context given to the model | S11, S12 | Must | 5.3 | src/commentary/number_check.py | Test: a draft with an invented number fails; a correct draft passes (SC-5) | Open |
| FR-13 | Record a status of Draft or Approved for each commentary, with reviewer role and time; allow editing before approval | S12, S04 | Must | 5.4 | src/commentary/review.py | Test: status change is stored and shown | Open |
| FR-14 | Let a cost-centre owner enter a short cause for a flagged item, and use it in the commentary | S07 | Should | 5.4 | src/commentary/review.py, context.py | Demo: entered cause appears in the regenerated draft | Open |
| FR-15 | Provide a dashboard with overview, site comparison, variance waterfall, flagged items with commentary, and data-quality report | S01, S05 | Must | 6 | app/dashboard.py | Walk-through; five values spot-checked against the variance table | Open |
| FR-16 | Offer commentary in German as an option | S03 | Could | 5.2 | src/commentary/llm.py | Demo: German draft passes the number check | Open |
| NFR-01 | Use synthetic data only; hold no person-level data; report personnel cost at cost-centre level only | S13, S11 | Must | 2 | src/generate_data.py | Review of data files and columns | Open |
| NFR-02 | Run end to end from raw files with one command in under two minutes, with identical results on every run | S02, S09 | Must | 3, 7.1 | src/pipeline/run.py | Timed run from an empty database (SC-6) | Open |
| NFR-03 | Make every reported figure traceable to its source file and row | S12 | Must | 3.1, 3.3 | src/pipeline/sql/ | Test: source_file and source_row filled on every row | Open |
| NFR-04 | Send only aggregated figures to the language model, and log every prompt, answer and check result | S11 | Must | 5.1, 5.3 | src/commentary/ | Review of the log file | Open |
| NFR-05 | Work without a language-model key by using template commentary | S02 | Must | 5.2 | src/commentary/llm.py | Test: run without a key produces commentary that passes the number check | Open |
| NFR-06 | Write transformations in SQL and keep mappings as tables so the logic can move to a central data platform or to KNIME | S10, S02 | Should | 3, 7.2 | src/pipeline/sql/, knime/ | KNIME workflow reproduces the harmonised table totals | Open |
| NFR-07 | Cover transformation and variance logic with automated tests | S12 | Must | 7.1 | tests/ | All tests pass (SC-7) | Open |
| NFR-08 | Show on every screen and document that the data is synthetic and the project is independent | S11 | Must | 6, 7.3 | app/dashboard.py, README.md | Review | Open |

## 3. Summary by priority

| Priority | Count | Rule |
|---|---|---|
| Must | 21 | Required for acceptance |
| Should | 3 | Delivered if the schedule holds |
| Could | 1 | Delivered only if time is left after milestone M5 |

## 4. Status values

- **Open:** not started.

- **Built:** implemented, not yet verified.

- **Verified:** the verification in the matrix has passed.

- **Removed:** taken out through the change log in document 07.
