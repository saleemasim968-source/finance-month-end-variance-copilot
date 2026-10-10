# Build log

A record of each stage of the build, written as it happened. For every stage it lists what was built, which files changed, what was decided, the quality gate result and the requirement status. Decisions and changes are also collected for document 07 in `docs/log_entries_for_07.md`; this log points to them by ID.

Each stage is one Git commit. The hash is shown in `git log --oneline`.

---

## Stage 0: Planning (WBS 1.1, 1.2), 10 Oct

**Built**
- Converted documents 01–08 to markdown (`docs/md/`).
- `CLAUDE.md`: build rules and a summary of the specification.
- `docs/architecture.md`: layers, data model, storage, commentary controls, test strategy.
- `docs/log_entries_for_07.md`: proposed decisions, issues and open questions.
- Git repository and public GitHub repo `finance-month-end-variance-copilot`; folder skeleton per doc 04 §7; minimal README with the synthetic-data notice.

**Decided:** D-009 to D-022 and C-001 to C-004, all approved by the PM.
**Found:** 17 ambiguities in documents 01–08 (A-01 to A-17, plus A-18 during architecture). All were resolved.
**Milestone:** M1, green.

---

## Stage 1: WP 2, data foundation (WBS 2.1, 2.2), 10 Oct

**Built**
| File | Purpose |
|---|---|
| `src/generate_data.py` | Deterministic synthetic data generator, with the planted events and data issues (written with PM permission, D-023; now frozen) |
| `data/raw/*.csv`, `data/reference/fx_rates.csv` | Generated input |
| `data/reference/account_mapping.csv`, `cost_centre_mapping.csv`, `cost_behaviour.csv` | Maintained reference tables (WBS 2.2) |
| `tests/test_data_foundation.py` | WP 2 quality gate, 17 tests |
| `requirements.txt` | Pinned packages |

**Decided:** D-023 to D-026 (approved).
**Quality gate:** passed. Row counts are 216/216/433/27/9 and every local code is mapped. Removing a mapping on purpose made the test fail. A pre-check found exactly 3 spend flags and 3 volume flags (A-13).
**Requirements:** NFR-01 verified; FR-04 built.

---

## Stage 2: WP 3, ELT pipeline (WBS 3.1–3.4), 10 Oct

**Built**
| File | Purpose |
|---|---|
| `src/pipeline/ingest.py` | Raw load: files into DuckDB unchanged, plus file and line number |
| `src/pipeline/sql/staging/*.sql` | Per-site cleaning: periods, units, currency, duplicates, BUD/ACT pivot |
| `src/pipeline/sql/checks/unmapped_codes.sql` | Mapping gate |
| `src/pipeline/sql/reporting/01_harmonised.sql` | Harmonised reporting table (648 rows) |
| `src/pipeline/sql/quality/*.sql` | Data-quality report and reconciliation |
| `src/pipeline/quality.py` | Runs the gate and checks; stops with one clear message |
| `src/pipeline/run.py` | One-command rebuild |
| `config.yaml`, `pytest.ini`, `src/__init__.py`, `src/pipeline/__init__.py` | Configuration and technical glue |
| `tests/test_pipeline.py` | WP 3 quality gate, 15 tests |

**Decided:** D-027 to D-031 (approved).
**Quality gate:** passed. 54/54 reconciliation checks at EUR 0.00 difference; both planted data issues reported; 32/32 tests. Deleting a harmonised row on purpose made the reconciliation stop the run.
**Requirements:** FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, NFR-03 verified; NFR-02 and NFR-06 built.
**Milestone:** M2, green.

---

## Stage 3: WP 4, variance analytics (WBS 4.1–4.3), 10 Oct

From here on, the PM asked for the whole build to be completed in one go, with every stage logged here for later review.

**Built**
| File | Purpose |
|---|---|
| `src/analytics/variance.py` | Flexed budget, total variance, volume and spend effect, spend and volume flags, cost per wafer, list of flagged items |
| `src/analytics/__init__.py` | Package marker |
| `config.yaml` | New `materiality` section (EUR 50,000 and 5 %, 5 % volume) |
| `src/pipeline/run.py` | Now runs analytics as the last step and prints the flag counts |
| `tests/conftest.py` | One shared pipeline run for all tests |
| `tests/test_variance.py` | WP 4 quality gate, 12 tests (3 on a hand-calculated example, 9 on the real data) |

**Decided:** D-032 (flagged-items table with a stable key), D-033 (analytics inside the one-command run).
**Results:**
- Spend flags: NORTH May Lithography Maintenance (+EUR 477k, +156.9 %); ALPS Jul and Aug Facilities Energy (+EUR 106k / +21.8 %, +EUR 115k / +23.7 %).
- Volume flags: ASIA Jul, Aug, Sep (about −14.5 %).
- ALPS Sep cost per wafer marked incomplete (missing actual).
**Quality gate:** passed. volume + spend = total on all 647 posted rows (largest difference 0.0); exactly the three planted events flagged; 44/44 tests.
**Requirements:** FR-07, FR-08, FR-09, FR-10 verified. SC-4 met.
**Milestone:** M3, green.

---

## Stage 4: WP 5, AI commentary (WBS 5.1–5.4), 10 Oct

**Built**
| File | Purpose |
|---|---|
| `src/commentary/context.py` | Builds the rounded figures for one flagged item: the only input the model gets |
| `src/commentary/llm.py` | Claude client (official SDK) and a fixed template in English and German |
| `src/commentary/number_check.py` | Finds every number in a text and rejects any that is not in the context |
| `src/commentary/review.py` | Review store: Draft/Approved, reviewer role and time, edits, owner causes (`data/review/review.duckdb`) |
| `src/commentary/run.py` | Drafts all flagged items: generate, check, retry once, fall back to the template, log, store |
| `config.yaml` | New `commentary` section (language, store and log paths) |
| `src/pipeline/run.py` | Now drafts commentary for new flagged items at the end of the run |
| `tests/conftest.py` | Tests force the template writer and use temporary review and log files |
| `tests/test_commentary.py` | WP 5 quality gate, 21 tests |

**Decided:** D-034 to D-037. **Issue:** I-005 (no API key, so the live model path is untested against the real API).
**Quality gate:** passed. All 6 drafts pass the number check. A fake model that invents numbers is rejected, retried once with feedback, then replaced by the template; all three steps are logged. A text with an invented number cannot be approved. 65/65 tests.
**Requirements:** FR-11, FR-12, FR-13, FR-14, FR-16, NFR-04, NFR-05 verified. SC-5 met.
**Milestone:** M4, amber (live Claude call not yet exercised).

---

## Stage 5: WP 6, backend and frontend (WBS 6), 10 Oct

The PM asked for a frontend and a backend to show the prototype. This replaces the Streamlit dashboard in the plan (change C-005).

**Built**
| File | Purpose |
|---|---|
| `app/backend/main.py` | FastAPI app: JSON API for every view, review actions, pipeline rebuild; serves the frontend and a local copy of Plotly.js |
| `app/backend/queries.py` | Read-only SQL behind each view; sums over the selection only, no recalculation |
| `app/backend/__main__.py` | `python -m app.backend`: loads `.env`, builds data if missing, starts the server |
| `app/frontend/index.html`, `styles.css`, `app.js` | Single-page frontend: Overview, Site comparison, Variance bridge, Flagged items (edit / regenerate EN-DE / approve / reopen / owner cause), Data quality; light and dark theme; synthetic-data notice on every screen |
| `.env.example` | Where to put an optional `ANTHROPIC_API_KEY` |
| `src/commentary/llm.py` | New `load_env_file()` |
| `tests/test_dashboard.py` | WP 6 quality gate, 15 tests through the real API |

**Checked by eye:** screenshots of every view in light mode, dark mode and narrow width. Three fixes came out of that: the site filter showing on the wrong tab, an unreadable bridge drawn from zero, and the chart grid overflowing on phones.
**Decided:** C-005 (needs sponsor sign-off), D-038, D-039.
**Quality gate:** passed. Five named spot checks plus every chart's sums equal the variance table; the bridge closes from plan to actual for every site; review workflow works end to end through the API; 80/80 tests.
**Requirements:** FR-15 and FR-14 verified; NFR-08 built (README part in WP 7).
**Milestone:** M5, scope amber only because C-005 awaits sponsor sign-off.
