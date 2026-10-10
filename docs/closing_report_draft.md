# Closing report and lessons learned: draft for document 08

*Draft prepared by the AI coding assistant on 10 Oct 2026 for the project manager to review, correct and copy into document 08 (VC-08). Independent portfolio project; all data synthetic. Lessons learned are the assistant's observations and need the PM's own view added.*

## 1. Result against success criteria

| ID | Criterion | Target | Result | Met |
|---|---|---|---|---|
| SC-1 | Rows mapped to group structure | 100 % | 648 of 648 harmonised rows mapped | Yes |
| SC-2 | Reconciliation to source totals | Below 0.01 % | 54 of 54 site-period-measure checks, largest difference EUR 0.00 (see D-031 for what the check covers) | Yes |
| SC-3 | Planted data issues detected | 2 of 2 | Duplicate (FAB_ASIA, Jun, MY-ETC, M400, line 262) and missing actual (FAB_ALPS, Sep, KST-220, 6500, line 205) | Yes |
| SC-4 | Planted business events flagged | 3 of 3 | Tool-down, energy spike (Jul and Aug) and weak loading (Jul–Sep); no other flags | Yes |
| SC-5 | Commentary figures traceable | 100 % | Enforced: only a draft that passes the number check can be approved; invented numbers are rejected in tests. No live-model drafts yet (I-005) | Yes (template drafts); live model to confirm |
| SC-6 | End-to-end run time | Under 2 minutes | 0.91 s wall clock from an empty database (`docs/evidence/run_log.txt`) | Yes |
| SC-7 | Automated tests | All passing | 84 of 84 (`docs/evidence/test_report.txt`) | Yes |
| SC-8 | Business case delivered | One page | `docs/business_case.md`, estimates with assumptions | Delivered; PM review pending |

## 2. Requirements delivered

| Priority | Planned | Verified | Built, not verified | Removed | Comment |
|---|---|---|---|---|---|
| Must | 21 | 20 | 1 | 0 | BR-01 needs the PM's review against SC-8 |
| Should | 3 | 2 | 1 | 0 | NFR-06: the SQL part is done; the KNIME workflow must be built by hand (guide and parity check in `knime/`) |
| Could | 1 | 1 | 0 | 0 | FR-16 German commentary |

Changes needing sponsor sign-off (simulated): C-001 (two source-line columns), C-003 (missing-actual rule, FR-08 wording), C-005 (backend and frontend instead of Streamlit).

## 3. Schedule performance

The build ran on Saturday 10 Oct instead of across the weekend. Every milestone (M1–M5) was reached on Saturday, ahead of its planned time. M6 (closing and demo rehearsal) is open until the PM has reviewed this report and rehearsed the demo. From WP 4 on, the PM asked for the remaining packages to be built in one go, with each stage logged (`docs/build_log.md`) rather than a stop for review after each package.

## 4. Benefits

From `docs/business_case.md`. All figures are estimates.

| Benefit | Measure | Estimate | Assumption | How to validate |
|---|---|---|---|---|
| Less manual harmonisation | Hours per close | 7.5 h → 0.5 h | 2.5 h per site today | Time one real close |
| Faster commentary | Hours per close | 6.0 h → 1.5 h | 6 material items, 45 min each today | Controllers time the review of 10 drafts |
| Better comparability | Sites on one account structure | 3 of 3 | Mapping tables maintained | Mapping sign-off by site finance heads (S03) |
| Better traceability | Share of reported figures with lineage | 100 % | Source file and line on every row | Audit walk-through (S12) |

## 5. Lessons learned (assistant's observations; PM to add their own)

| Area | What went well | What to change next time |
|---|---|---|
| Planning and scope | Reading all eight documents first surfaced 18 gaps (A-01 to A-18) that were settled on paper, before any code depended on them | The generator was listed as existing but was missing (I-001); check that the inputs exist before baselining |
| Working with the AI coding assistant | One commit per work package, a build log and a decision log made each step reviewable; every check was also proved able to fail | The PM switched from a review after each package to one build; the review now happens afterwards, from the logs |
| Data and pipeline | Exact decimals and line-level lineage made the reconciliation balance to the cent | The reconciliation reuses the converted amounts (D-031); an independent conversion check would be stronger |
| AI commentary and controls | The number check, single retry, template fallback and approval lock work regardless of the model | The live model has not yet been tried (no key); run it once and review the drafts |
| Stakeholder view | Local codes sit beside group codes (S03); no person-level data (S13); the AI receives only aggregates (S11) | Real cost-behaviour shares need cost-centre owners (R07) |

## 6. Open items and next steps

- I-005: add an API key and review live Claude drafts (`python -m src.commentary.run --regenerate`).
- NFR-06: build the KNIME workflow from `knime/README.md` and run `knime/check_parity.py`.
- Sponsor sign-off for C-001, C-003 and C-005; PM review of the business case (BR-01).
- Copy the entries from `docs/log_entries_for_07.md` into document 07, and this draft into document 08.
- Follow-up ideas from the charter: AI-suggested account mapping, move to a central data platform, extension to investment tracking.

## 7. Handover

| Item | Location | Done |
|---|---|---|
| Source code, tagged version | GitHub `finance-month-end-variance-copilot`, tag `v1.0-prototype` | Yes |
| Project documents 01 to 08 | `docs/` (08 to be completed from this draft) | Partly |
| README and demo script | `README.md`, `docs/demo_script.md` | Yes |
| Sponsor acceptance (simulated) | Document 08 | Open |
