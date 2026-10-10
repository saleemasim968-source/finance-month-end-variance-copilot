# Proposed entries for document 07 (Decision, Change and Issue Log)

Working list kept during the build. The project manager copies approved entries into doc 07.
Status: OPEN = waiting for the PM's answer; PROPOSED = the assistant's suggested default.

## Issues

| ID | Date | Issue | Proposed action | Status |
|---|---|---|---|---|
| I-001 | 10 Oct | `src/generate_data.py` does not exist in the project folder (or anywhere under ~/Documents). Doc 04 §3 and WBS 2.1 say it exists and is complete. `data/raw/` and `data/reference/fx_rates.csv` are also missing. The WP 2 quality gate and all of WP 3 depend on these files. | PM to supply the file. Do not recreate it without a decision, because it is marked "do not change". | OPEN |
| I-002 | 10 Oct | (Resolved: `git init` done, repo created on GitHub.) The project folder was not a Git repository. Doc 03 §10 requires Git with at least one commit per work package. | `git init` before WP 2.2, with a `.gitignore` for `data/warehouse/`. | OPEN |
| I-003 | 10 Oct | The .docx files were in the project root, not in `docs/`. | They were copied to `docs/` and the originals left in the root. PM to decide whether to delete the root copies. | PROPOSED |
| I-004 | 10 Oct | The local Python is 3.14.7. Doc 03 asks for "3.11 or later", so this is compliant, but pinned versions of DuckDB, Streamlit and pandas must support 3.14. | Check at the start of WP 3. Fall back to a 3.12 venv if needed. | PROPOSED |

## Decisions (proposed defaults, to be confirmed)

| ID | Decision | Reason | Status |
|---|---|---|---|
| D-009 | Convert docs with python-docx through a one-off script outside the repo (pandoc is not installed). The output is in `docs/md/`. | Conversion is tooling, not product. | PROPOSED |
| D-011 | Public GitHub repository named `finance-month-end-variance-copilot`. | Portfolio visibility; the name states the domain (finance), the process (month-end close) and the product. All content is synthetic (D-001). | APPROVED by PM, 10 Oct |
| D-012 | Add `docs/architecture.md` as a planning artefact before WP 2.2. | Settle the design and open questions on paper before building (R04). | APPROVED by PM, 10 Oct |
| D-013 | Add a minimal `README.md` now, containing the synthetic-data notice. The full README is still WBS 7.3. | A public repo must show the notice from the first commit (NFR-08, R05). | PROPOSED |
| D-010 | Pending log entries are collected in `docs/log_entries_for_07.md`, not edited into the .docx directly. | The PM owns doc 07. | PROPOSED |

## Ambiguities and contradictions found in documents 01–08

| # | Where | Problem | Proposed resolution | Status |
|---|---|---|---|---|
| A-01 | 04 §4.1 vs NFR-03 | The harmonised table has one row per site × period × area × account with plan **and** actual, but only one `source_row` column. For FAB_ASIA, plan (BUD) and actual (ACT) come from two different source rows, so one column cannot trace both. | Use `source_row_plan` and `source_row_actual`. This deviates from §4.1 and needs a doc 07 change entry. Alternative: store "12;217". | OPEN |
| A-02 | 04 §4.2 reconciliation | It doesn't say whether plan and actual are reconciled separately or as one combined total. | Reconcile plan and actual separately (stricter). | OPEN |
| A-03 | 04 §4.2 | The duplicate rule says "keep one, log each removal", and reconciliation says "source = harmonised + logged corrections". The direction and sign of a correction aren't defined. | A correction = the amount removed (positive), so source total = harmonised total + Σ removed amounts. | PROPOSED |
| A-04 | 01 SC-2 vs FR-03 | SC-2 says "at the reference FX rate" and FR-03 says "monthly FX rate". It's unclear whether these are the same thing. | Both mean the monthly rate in `fx_rates.csv`. | PROPOSED |
| A-05 | 04 §4.2/4.3 | For the missing actual (ALPS Sep KST-220 6500), the docs say "exclude it from variance flags" but don't say what happens to total variance, spend effect and **actual cost per wafer** for ALPS Sep. Summing with NULL skipped understates actual cost per wafer. The FR-08 test "on every row" can't hold for a NULL row. | Keep actual_eur NULL; total and spend effect NULL; volume effect calculated; FR-08 test applies to rows with an actual; cost per wafer flagged as "incomplete" for ALPS Sep. | OPEN |
| A-06 | 02 C5 vs 05 FR-14 | Doc 02 says the commentary **must** use the owner's cause, but FR-14 is only a **Should**. | Doc 05 is the scope baseline, so treat FR-14 as Should. | PROPOSED |
| A-07 | 05 NFR-02 vs WP 5 | NFR-02 asks for "identical results on every run", but LLM output is non-deterministic. | Determinism applies to the pipeline and analytics (WP 3–4). Commentary is stored once and reused unless regenerated. | OPEN |
| A-08 | 04 §4.4 | The thresholds are "configuration values", but no config file appears in the repo structure (§7). | Add `config.yaml` at the repo root (or `src/config.py`). This needs a doc 04 §7 update. | OPEN |
| A-09 | 05 BR-01 vs 04 §7; 08 §8 | BR-01 puts the business case in `docs/business_case`, which isn't in the repo structure. Doc 08 puts the demo script in the repo root, and doc 04 doesn't mention a demo script file. | `docs/business_case.md`, `docs/demo_script.md`. | PROPOSED |
| A-10 | 04 §4.5, NFR-04 | No location is given for the prompt/answer/check log, or for where commentary status and owner causes are stored. | Use DuckDB tables `commentary`, `owner_cause`, and a JSONL log in `logs/`. Decide in WP 5. | OPEN (WP 5) |
| A-11 | 04 §4.2 | "Source row" numbering isn't defined: 1-based data row, or file line number including the header? | Use the 1-based physical file line (header = line 1), so a user can open the file and find it. | PROPOSED |
| A-12 | 04 §4.2 | "Unmapped code: stop the run" (hard fail) vs FR-06 "detect and **report** ... unmapped codes". | Report all unmapped codes in one error message, then stop. Don't stop at the first one. | PROPOSED |
| A-13 | 04 §5 | The spike is "22% above expected in **all areas**", but only Facilities is expected to flag. This depends on the generator's amounts, since the other areas must stay below EUR 50k. It can't be checked until the generator exists (I-001). | Verify in WP 4. | OPEN |
| A-14 | 04 §3 | The CSV encoding of the ALPS file isn't stated (German names may contain umlauts), and neither are the period formats of `wafer_volumes.csv` and `fx_rates.csv` or the site labels used in them. | Inspect the generator output in WP 3.1. | OPEN |
| A-15 | 04 §3.1 | `account_mapping.csv` includes `local_account_name`, but the local names (e.g. for FAB_ALPS and FAB_ASIA) aren't given in any document. | Take the names from the generator output; join on code only, and treat the name as informational. | OPEN |
| A-16 | 03 §3 | The AI assistant "reads documents 01 to 06", but 07 and 08 are also needed (07 for logging). | No action; all eight were read. | PROPOSED |
| A-17 | 03 §6 vs 04 §6 | The schedule gives WBS 2 an hour (16:30–17:30), but 2.1 is already complete, so the hour covers 2.2 only. | No action. | PROPOSED |
| A-18 | 03 NFR-02 vs 04 §4.5 | Rebuilding the warehouse on every run (needed for identical results) would wipe commentary approvals and owner causes. | Keep review state in a separate `data/review/review.duckdb` that the pipeline does not rebuild (architecture §4). | PROPOSED |
