# Entries for document 07 (Decision, Change and Issue Log)

Working list kept during the build. The project manager copies entries into doc 07.
Status: OPEN = waiting for an answer · PROPOSED = the assistant's suggestion · APPROVED = accepted by the PM (date).

## Decisions

| ID | Date | Decision | Reason | Decided by |
|---|---|---|---|---|
| D-009 | 10 Oct | Convert the docs with python-docx through a one-off script outside the repo (pandoc is not installed). The output is in `docs/md/`. | Conversion is tooling, not product. | PM (approved 10 Oct) |
| D-010 | 10 Oct | Collect pending log entries in `docs/log_entries_for_07.md`, not directly in the .docx. | The PM owns doc 07. | PM (approved 10 Oct) |
| D-011 | 10 Oct | Public GitHub repository `finance-month-end-variance-copilot`. | Portfolio visibility. The name states the domain, the process and the product. All content is synthetic (D-001). | PM (approved 10 Oct) |
| D-012 | 10 Oct | Add `docs/architecture.md` as a planning artefact before WP 2.2. | Settle the design on paper before building (R04). | PM (approved 10 Oct) |
| D-013 | 10 Oct | A minimal `README.md` with the synthetic-data notice from the first commit. The full README is still WBS 7.3. | Public repo (NFR-08, R05). | PM (approved 10 Oct) |
| D-014 | 10 Oct | A correction in the reconciliation = the amount removed (positive): source total = harmonised total + Σ removed amounts. (A-03) | Makes the doc 04 §4.2 rule calculable. | PM (approved 10 Oct) |
| D-015 | 10 Oct | "Reference FX rate" (SC-2) = the monthly rate in `fx_rates.csv` (FR-03). (A-04) | One rate source. | PM (approved 10 Oct) |
| D-016 | 10 Oct | FR-14 stays a "Should", although doc 02 C5 says "must". Doc 05 is the scope baseline. (A-06) | Keeps the baseline consistent. | PM (approved 10 Oct) |
| D-017 | 10 Oct | NFR-02 "identical results" applies to the pipeline and analytics (WP 3–4). Commentary is generated once, stored, and reused unless explicitly regenerated. (A-07) | LLM output is not deterministic. | PM (approved 10 Oct) |
| D-018 | 10 Oct | The business case goes in `docs/business_case.md` and the demo script in `docs/demo_script.md`. (A-09) | Paths were not defined consistently. | PM (approved 10 Oct) |
| D-019 | 10 Oct | Review state goes in `data/review/review.duckdb`, which the pipeline doesn't rebuild. The LLM log goes in `logs/llm_log.jsonl`. (A-10, A-18) | Approvals must survive a rebuild of the warehouse. | PM (approved 10 Oct) |
| D-020 | 10 Oct | Source line = physical line in the file, with the header as line 1. (A-11) | A user can open the file and find the line. | PM (approved 10 Oct) |
| D-021 | 10 Oct | The mapping gate reports **all** unmapped codes in one error, then stops the run. (A-12) | Satisfies both "stop" (doc 04 §4.2) and "report" (FR-06). | PM (approved 10 Oct) |
| D-022 | 10 Oct | Join mappings on the local code only. `local_account_name` is informational and is taken from the generator output. (A-15) | Local names are not specified in any document. | PM (approved 10 Oct) |

## Change log
Per doc 03 §5.5, changes that touch a "Must" requirement or its verification need **sponsor approval (simulated)** in addition to the PM's approval.

| ID | Date | Change requested | Impact | Decision | Documents to update |
|---|---|---|---|---|---|
| C-001 | 10 Oct | Harmonised table: replace `source_row` with `source_line_plan` and `source_line_actual`. (A-01) | Scope: none; it makes NFR-03 achievable for FAB_ASIA, where plan and actual are separate lines. Schedule: none. Risk: lowers R03. | Approved by PM 10 Oct; **sponsor sign-off needed** (concerns how Must NFR-03 is met) | 04 §4.1 |
| C-002 | 10 Oct | Reconcile plan and actual **separately** per site and period. (A-02) | Stricter than doc 04 §4.2; no schedule impact. | Approved by PM 10 Oct | 04 §4.2 |
| C-003 | 10 Oct | Missing actual: actual_eur, total variance and spend effect stay NULL; the volume effect is still calculated; the FR-08 test covers **posted** rows only; actual cost per wafer is marked "incomplete" where an actual is missing. (A-05) | Changes the FR-08 verification wording ("every row" → "every posted row"). | Approved by PM 10 Oct; **sponsor sign-off needed** (verification of Must FR-08) | 04 §4.2–4.3, 05 FR-08 |
| C-004 | 10 Oct | Repository additions: `config.yaml` (thresholds, A-08), `docs/architecture.md`, `docs/log_entries_for_07.md`, `CLAUDE.md`, `data/review/`, `logs/`. | None on scope; makes the "configuration values" in doc 04 §4.4 concrete. | Approved by PM 10 Oct | 04 §7 |

## Issue log

| ID | Date | Issue | Action | Status |
|---|---|---|---|---|
| I-001 | 10 Oct | `src/generate_data.py` doesn't exist in the project (or under ~/Documents), although doc 04 §3 and WBS 2.1 say it's complete. `data/raw/` and `fx_rates.csv` are missing as well. This blocks the WP 2 quality gate and all of WP 3. | PM to supply the file. It must not be recreated without a decision, because it is marked "do not change". | **OPEN** |
| I-002 | 10 Oct | The project folder was not a Git repository (doc 03 §10). | `git init`; public repo created and first commit pushed. | Closed 10 Oct |
| I-003 | 10 Oct | The .docx files were in the project root, not in `docs/`. | Copied to `docs/`; root copies left in place and gitignored. PM may delete them. | Closed 10 Oct |
| I-004 | 10 Oct | Local Python is 3.14.7 (compliant with "3.11 or later"). The pinned DuckDB, Streamlit and pandas versions must support it. | Check at the start of WP 3; fall back to a 3.12 venv if needed. | Open (WP 3) |

## Items to verify once the generator exists

| # | Item | When |
|---|---|---|
| A-13 | The ALPS energy spike hits all areas, but only Facilities should cross EUR 50k (expected 3 spend flags). | WP 4 |
| A-14 | ALPS file encoding; period formats and site labels in `wafer_volumes.csv` and `fx_rates.csv`. | WP 3.1 |

## Notes (no action)

- A-16: doc 03 §3 says the assistant reads docs 01–06; all eight were read.
- A-17: the WBS 2 slot in the schedule (16:30–17:30) covers 2.2 only, because 2.1 is complete.
