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
| D-023 | 10 Oct | `src/generate_data.py` was written by the AI assistant with the PM's permission, because the file did not exist (I-001). From the WP 2 review on, it is frozen: "do not change" applies. | Unblocks WBS 2 and 3. It deviates from doc 04 §3 and WBS 2.1, which say the file already exists. | PM (permission 10 Oct) |
| D-024 | 10 Oct | The parentheses in doc 04 §3 describe formats, not column names: e.g. FAB_ASIA columns are `Version` (values BUD/ACT) and `Amount` (MYR); FAB_NORTH `period` holds `2026-01`. `wafer_volumes.csv` and `fx_rates.csv` use `FAB_NORTH`-style site labels and `YYYY-MM` periods. All files are UTF-8; the ALPS file contains one umlaut (`Wärme`). (A-14) | Doc 04 §3 was ambiguous. | PM (approved 10 Oct) |
| D-025 | 10 Oct | The generator uses a fixed seed (20261010), Python standard library only, and noise bands (plan ±3 %, spend ±2 %, volume ±2.5 %) well inside the 5 % thresholds, so that only planted events can flag. | Determinism (NFR-02) and the exact 3 + 3 flag expectation in doc 04 §5. | PM (approved 10 Oct) |
| D-026 | 10 Oct | WBS 2.1 and 2.2 were built in one step, because the quality gate in doc 03 §7 is defined for WBS 2 as a whole. | The gate needs both the generator and the mappings. | PM (approved 10 Oct) |
| D-027 | 10 Oct | `rpt_harmonised` has an extra column `actual_posted` (true/false) next to the doc 04 §4.1 columns. | Doc 04 §4.2 says to "mark" a row whose actual is missing; a column marks it on the row itself, and WP 4 uses it to exclude the row from flags. | PM (approved 10 Oct) |
| D-028 | 10 Oct | The SQL is split into `sql/staging`, `sql/checks` (mapping gate), `sql/reporting` and `sql/quality`, with files run in name order. `src/__init__.py`, `src/pipeline/__init__.py` and `pytest.ini` were added so modules and tests can import each other. | Doc 04 §7 names only "a sql/ folder with staging and reporting queries". | PM (approved 10 Oct) |
| D-029 | 10 Oct | Amounts are fixed-point decimals (cents), not floating point. FAB_ASIA lines are converted to EUR and rounded to cents per line, before plan and actual are combined. | Floating-point sums can differ between runs (NFR-02). Rounding per line keeps the reconciliation exact. | PM (approved 10 Oct) |
| D-030 | 10 Oct | The exact-duplicate rule is applied to all three site files, not only FAB_ASIA. A missing FX rate, an unknown Version value, a malformed period or a wrong number of fields stops the run with the file and line named. | Doc 04 §4.2 says "a source file"; failing loudly is safer than dropping data (R03). | PM (approved 10 Oct) |
| D-031 | 10 Oct | The reconciliation's "source total" is the sum of every source line in EUR, taken from the line-level staging tables (one row per raw line, duplicates included; a test checks the row counts match). It proves no amount is lost or added by de-duplication, pivoting and mapping. It does **not** independently re-check the currency and TEUR conversion; separate tests compare converted values against the raw files instead. | Honest statement of what the check covers. | PM (approved 10 Oct) |
| D-032 | 10 Oct | WP 4 adds `an_flagged_items`: one row per item needing commentary, with a stable `item_id` (e.g. `spend\|FAB_NORTH\|2026-05\|Lithography\|Maintenance`). The review store uses this key, so approvals reattach after a rebuild. | Links WP 4 to WP 5 (A-18). | AI assistant (PM delegated, 10 Oct) |
| D-033 | 10 Oct | Analytics run inside `src/pipeline/run.py` after the reconciliation; results are written back to DuckDB. Calculations use floating point; the identity checks use a tolerance of 1e-6 EUR. | One command (NFR-02); pandas per doc 03 §10. | AI assistant (PM delegated, 10 Oct) |
| D-034 | 10 Oct | Language model: Claude through the official Anthropic SDK. Model from `LLM_MODEL` (default `claude-opus-5-5`), low effort (short texts), 20 s timeout, no automatic retries, server-side refusal fallback enabled. `LLM_PROVIDER=auto` calls the API only when `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` is set; otherwise the template is used. | Doc 03 §10 leaves the provider open. Spending money only with a deliberately set key protects the EUR 5 cap. | AI assistant (PM delegated, 10 Oct) |
| D-035 | 10 Oct | Context and number check: amounts in whole EUR thousands, percentages with one decimal. Volume items also get wafer counts and cost per wafer. The local codes of the item are in the context and ignored by the check, like period labels. A number passes if its absolute value equals a context figure or a number in the owner's cause. | Makes doc 04 §4.5 precise. | AI assistant (PM delegated, 10 Oct) |
| D-036 | 10 Oct | New file `src/commentary/run.py` drafts all flagged items. The one-command pipeline run calls it at the end for items without commentary. | Doc 04 §7 lists no orchestrator; SC-6 asks for one command up to the dashboard data. | AI assistant (PM delegated, 10 Oct) |
| D-037 | 10 Oct | Review rules: edit only while Draft (every edit re-checked); approve only a Draft that passes the check; an approved text is locked until reopened; regeneration never overwrites an approved text. | No unchecked figure can be released (SC-5, D-008). | AI assistant (PM delegated, 10 Oct) |
| D-038 | 10 Oct | Dashboard rules: variance views use posted rows only, so plan + volume + spend = actual holds; the not-posted row is named on the overview. The bridge starts at zero (volume effect, spend effect per cost type, total variance) because a bridge drawn from EUR 266m hides every effect. Colours follow the validated dataviz palette: sites have fixed colours, red/blue diverging for above/below plan, status always with a label. | Every dashboard figure must equal the variance table (doc 03 §7) and be readable. | AI assistant (PM delegated, 10 Oct) |
| D-039 | 10 Oct | The frontend has a "Rebuild data" button that runs the pipeline. One lock serialises all data access in the backend (single-user prototype). Views can be linked with `#overview`, `#sites`, `#bridge`, `#flags`, `#quality`, and `?theme=dark`. | Demo convenience; safe concurrent access to DuckDB. | AI assistant (PM delegated, 10 Oct) |
| D-022 | 10 Oct | Join mappings on the local code only. `local_account_name` is informational and is taken from the generator output. (A-15) | Local names are not specified in any document. | PM (approved 10 Oct) |

## Change log
Per doc 03 §5.5, changes that touch a "Must" requirement or its verification need **sponsor approval (simulated)** in addition to the PM's approval.

| ID | Date | Change requested | Impact | Decision | Documents to update |
|---|---|---|---|---|---|
| C-001 | 10 Oct | Harmonised table: replace `source_row` with `source_line_plan` and `source_line_actual`. (A-01) | Scope: none; it makes NFR-03 achievable for FAB_ASIA, where plan and actual are separate lines. Schedule: none. Risk: lowers R03. | Approved by PM 10 Oct; **sponsor sign-off needed** (concerns how Must NFR-03 is met) | 04 §4.1 |
| C-002 | 10 Oct | Reconcile plan and actual **separately** per site and period. (A-02) | Stricter than doc 04 §4.2; no schedule impact. | Approved by PM 10 Oct | 04 §4.2 |
| C-003 | 10 Oct | Missing actual: actual_eur, total variance and spend effect stay NULL; the volume effect is still calculated; the FR-08 test covers **posted** rows only; actual cost per wafer is marked "incomplete" where an actual is missing. (A-05) | Changes the FR-08 verification wording ("every row" → "every posted row"). | Approved by PM 10 Oct; **sponsor sign-off needed** (verification of Must FR-08) | 04 §4.2–4.3, 05 FR-08 |
| C-005 | 10 Oct | Replace the Streamlit dashboard (doc 03 §10; FR-15 planned in `app/dashboard.py`) with a separate backend and frontend: a FastAPI JSON API (`app/backend/`) and a plain HTML/JavaScript/Plotly.js frontend (`app/frontend/`). | Requested by the PM ("create frontend and backend to show my prototype"). Scope: FR-15 content unchanged, all five views delivered. Schedule: built within WP 6. Risk: R08 (demo failure) is handled by serving Plotly.js locally, so no internet is needed. | Requested and approved by PM, 10 Oct. FR-15 is a "Must", so **sponsor sign-off (simulated) needed** for the change of technology | 03 §10, 04 §7, 05 FR-15 location |
| C-004 | 10 Oct | Repository additions: `config.yaml` (thresholds, A-08), `docs/architecture.md`, `docs/log_entries_for_07.md`, `CLAUDE.md`, `data/review/`, `logs/`. | None on scope; makes the "configuration values" in doc 04 §4.4 concrete. | Approved by PM 10 Oct | 04 §7 |

## Issue log

| ID | Date | Issue | Action | Status |
|---|---|---|---|---|
| I-001 | 10 Oct | (Resolved by D-023.) `src/generate_data.py` didn't exist in the project (or under ~/Documents), although doc 04 §3 and WBS 2.1 say it's complete. `data/raw/` and `fx_rates.csv` are missing as well. This blocks the WP 2 quality gate and all of WP 3. | The PM gave permission to create it; written in WP 2. | Closed 10 Oct |
| I-002 | 10 Oct | The project folder was not a Git repository (doc 03 §10). | `git init`; public repo created and first commit pushed. | Closed 10 Oct |
| I-003 | 10 Oct | The .docx files were in the project root, not in `docs/`. | Copied to `docs/`; root copies left in place and gitignored. PM may delete them. | Closed 10 Oct |
| I-004 | 10 Oct | Local Python is 3.14.7 (compliant with "3.11 or later"). The pinned DuckDB, Streamlit and pandas versions must support it. | DuckDB 1.5.6 and PyYAML 6.0.3 install and run on 3.14; Streamlit and pandas are checked in WP 4/6. | Closed for WP 3 |
| I-005 | 10 Oct | No Anthropic API key is set on this machine, so the live Claude path has not been called. It is covered by tests with a fake model (good draft kept; invented numbers rejected, retried once, then template; errors fall back). | PM: add `ANTHROPIC_API_KEY` to `.env` and run `python -m src.commentary.run --regenerate` once to see live drafts. | Open |

## Items to verify once the generator exists

| # | Item | When |
|---|---|---|
| A-13 | Pre-checked in WP 2 with a throwaway script: the data gives exactly 3 spend flags (NORTH May CC1010/440000 +EUR 477k; ALPS Jul and Aug KST-900/6200 +EUR 106k and +115k) and 3 volume flags (ASIA Jul–Sep, −14.2 % to −14.5 %). No other row reaches 60 % of either threshold. Formal test still in WP 4. | WP 4 |
| A-14 | Resolved by D-024. | Done |

## Notes (no action)

- A-16: doc 03 §3 says the assistant reads docs 01–06; all eight were read.
- A-17: the WBS 2 slot in the schedule (16:30–17:30) covers 2.2 only, because 2.1 is complete.

## Requirement status updates for doc 05

| ID | New status | Evidence | Date |
|---|---|---|---|
| NFR-01 | Verified | `tests/test_data_foundation.py::test_no_person_level_data`; review of all column headers; data is generated synthetic data only | 10 Oct (WP 2) |
| FR-04 | Built (mapping tables only), superseded below | `data/reference/*.csv`; coverage test passes, and fails when a mapping is removed. The "unknown code stops the run" test belongs to WP 3.3. | 10 Oct (WP 2) |
| FR-01 | Verified | `test_fr01_raw_tables_have_one_row_per_file_line` | 10 Oct (WP 3) |
| FR-02 | Verified | `test_fr02_nine_periods_per_site_in_yyyy_mm` | 10 Oct (WP 3) |
| FR-03 | Verified | 54 of 54 reconciliation checks pass with a difference of EUR 0.00; TEUR and MYR conversion tests | 10 Oct (WP 3) |
| FR-04 | Verified | 648 of 648 rows mapped (SC-1); `test_fr04_unknown_codes_stop_the_run_and_are_all_reported` | 10 Oct (WP 3) |
| FR-05 | Verified | `test_fr05_local_codes_are_kept_on_every_row` | 10 Oct (WP 3) |
| FR-06 | Verified | Exactly one duplicate and one missing actual reported (SC-3); duplicate logged as a correction | 10 Oct (WP 3) |
| NFR-03 | Verified | `test_nfr03_every_row_points_to_its_source_lines` opens each source file at the recorded line for all 648 rows | 10 Oct (WP 3) |
| NFR-02 | Built | Pipeline: 0.53 s and identical results on two runs. Full verification (clean run of the whole product) in WP 7.1 | 10 Oct (WP 3) |
| NFR-06 | Built (SQL part) | All transformations are SQL; mappings are tables. KNIME part in WP 7.2 | 10 Oct (WP 3) |
| FR-07 | Verified | `test_fr07_total_variance_is_actual_minus_plan` | 10 Oct (WP 4) |
| FR-08 | Verified | volume + spend = total on all 647 posted rows (C-003); hand-calculated unit test | 10 Oct (WP 4) |
| FR-09 | Verified | exactly the 3 planted spend events and 3 volume events (SC-4); thresholds in `config.yaml` | 10 Oct (WP 4) |
| FR-10 | Verified | cost per wafer equals total cost / wafers for all 27 site-periods | 10 Oct (WP 4) |
| FR-11 | Verified | Drafts reviewed for all 6 flagged items (template writer); context holds calculated figures only | 10 Oct (WP 5) |
| FR-12 | Verified | Invented, derived and re-rounded numbers fail; correct drafts pass (SC-5) | 10 Oct (WP 5) |
| FR-13 | Verified | Status, reviewer role and time stored and read back; edit before approval; lock after approval | 10 Oct (WP 5) |
| FR-14 | Verified (test) | Entered cause appears in the regenerated draft. Demo in the frontend in WP 6 | 10 Oct (WP 5) |
| FR-16 | Verified | German template drafts pass the number check for all 6 items | 10 Oct (WP 5) |
| NFR-04 | Verified | Context contains no row-level lineage; every prompt, answer and check result is in `logs/llm_log.jsonl` | 10 Oct (WP 5) |
| NFR-05 | Verified | Without a key the template is used and passes the number check | 10 Oct (WP 5) |
| FR-15 | Verified | Walk-through of all five views (screenshots); five values spot-checked by automated tests, plus the sums behind every view compared with the variance table | 10 Oct (WP 6) |
| FR-14 | Verified | Cause entered through the frontend/API appears in the regenerated draft | 10 Oct (WP 6) |
| NFR-08 | Built | Notice on every screen of the frontend (test). README part in WP 7.3 | 10 Oct (WP 6) |

## Milestone status entries

| Milestone | Planned | Actual | Schedule | Scope | Quality | Comment |
|---|---|---|---|---|---|---|
| M1 Documentation baselined | Sat 16:30 | Sat 10 Oct | Green | Green | Green | Docs 01–08 plus architecture baselined and approved |
| M2 Harmonised table reconciled | Sat 20:00 | Sat 10 Oct | Green | Green | Green | 648 rows, 54/54 reconciliation checks at EUR 0.00 difference, both planted data issues reported, 32 tests passing |
| M3 Variance engine tested | Sun 11:00 | Sat 10 Oct | Green | Green | Green | 3 + 3 flags exactly on the planted events; 44 tests passing |
| M4 Commentary with number check | Sun 13:30 | Sat 10 Oct | Green | Green | Amber | Number check, retry, fallback and review all tested; live Claude path not yet run (no API key, I-005) |
| M5 Dashboard complete | Sun 16:30 | Sat 10 Oct | Green | Amber | Green | Backend + frontend instead of Streamlit (C-005, needs sponsor sign-off); 80 tests passing |
