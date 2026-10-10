Month-End Variance Copilot

**Project Management Plan**

| Document ID | VC-03 |
|---|---|
| Process group | Planning |
| Version | 1.0 (baseline) |
| Date | 10 October 2026 |
| Project manager | Asim |
| Sponsor | Head of Frontend Cluster Finance (persona S01) |

Independent portfolio project. All data is synthetic and all stakeholders are assumed role personas. This is not a document of any real company and contains no internal or confidential information.

## 1. Purpose

This plan describes how the project is planned, executed, monitored, controlled and closed. It is the single reference for how work is managed. Subsidiary plans that would be separate documents on a large project are short sections here.

## 2. Tailoring decisions

The project is small, short and delivered by one person, so the PMBOK Guide processes were tailored. The table shows what is applied and what was deliberately left out.

| Knowledge area | Applied in this project | Tailored out, and why |
|---|---|---|
| Integration | Charter, this plan, change control, closing report | None |
| Scope | Scope statement, WBS, requirements traceability matrix | Separate WBS dictionary; work package descriptions are in document 04 |
| Schedule | Milestone schedule by work package (section 6) | Network diagram and critical path; the work is one sequential chain |
| Cost | Cost cap of EUR 5 for language model usage | Cost baseline and earned value; no meaningful spend |
| Quality | Quality gates per work package (section 7) | None |
| Resource | One person plus an AI coding assistant | Resource plan and team charter |
| Communications | Communication summary in document 02 | Separate communications plan |
| Risk | Qualitative risk register, document 06 | Quantitative risk analysis |
| Procurement | Not applicable | Nothing is purchased |
| Stakeholder | Stakeholder register and engagement actions, document 02 | None |

## 3. Life cycle and approach

- **Planning is predictive:** scope, requirements and success criteria are baselined before the build starts.

- **Delivery is incremental:** the product is built in six work packages. Each one ends with a quality gate and a working result.

- **The documents drive the build:** the AI coding assistant reads documents 01 to 06 as its specification and implements one work package at a time.

## 4. Baselines

| Baseline | Where defined | Change needs |
|---|---|---|
| Scope | Document 04, Scope Statement and WBS; document 05, Requirements Traceability Matrix | Entry in the change log; sponsor approval for "Must" requirements |
| Schedule | Section 6 of this plan | Entry in the change log |
| Cost | EUR 5 cap | Sponsor approval |

## 5. Requirements management plan

### 5.1 Collection

Requirements are derived from the stakeholder personas in document 02, from the conflicts listed there, and from the public job description that motivated the project. On a real project they would be collected through interviews with controllers and a walk-through of one month-end close.

### 5.2 Identification and types

- **BR:** business requirement, for example a documented benefit.

- **FR:** functional requirement, something the solution does.

- **NFR:** non-functional requirement, a condition the solution meets.

Each requirement has a unique ID that never changes and is never reused.

### 5.3 Prioritisation

Requirements are prioritised with MoSCoW. "Must" items define the minimum accepted product. "Should" items are delivered if the schedule holds. "Could" items are delivered only if time is left after milestone M5.

### 5.4 Traceability

Document 05 links every requirement to its source stakeholder, its WBS work package, the planned code file and the test or check that verifies it. A requirement without a verification method is not accepted into the baseline.

### 5.5 Change control

- Any change to a requirement is recorded in document 07 with reason and impact on scope, schedule and risk.

- The project manager decides on "Should" and "Could" requirements.

- The sponsor decides on "Must" requirements and on success criteria.

- After approval, documents 04 and 05 are updated and the version number is raised.

### 5.6 Acceptance

A requirement is complete when its verification in document 05 passes and the status is set to "Verified". The product is accepted when all "Must" requirements are verified and all success criteria in the charter are met.

## 6. Schedule

| WBS | Work package | Start | Finish | Milestone |
|---|---|---|---|---|
| 1.1, 1.2 | Initiating and planning documents | Sat 13:30 | Sat 16:30 | M1 |
| 2 | Data foundation: synthetic data and reference tables | Sat 16:30 | Sat 17:30 |  |
| 3 | ELT pipeline, data-quality checks, reconciliation | Sat 17:30 | Sat 20:00 | M2 |
| 4 | Variance analytics | Sun 09:00 | Sun 11:00 | M3 |
| 5 | AI commentary, number check, review workflow | Sun 11:00 | Sun 13:30 | M4 |
| 6 | Dashboard | Sun 14:30 | Sun 16:30 | M5 |
| 7 | Validation and transfer: tests, KNIME, README, demo script, business case | Sun 16:30 | Sun 19:00 |  |
| 1.4 | Closing report and lessons learned | Sun 19:00 | Sun 19:30 | M6 |

Schedule control rule: if a milestone slips by more than one hour, the lowest-priority open requirement is removed through the change log.

## 7. Quality management

Quality is built in through a gate at the end of each work package. A work package is not closed until its gate is passed.

| WBS | Quality gate | Evidence |
|---|---|---|
| 2 | Data files exist with the specified row counts; reference tables cover every local code | Generator output; mapping coverage check |
| 3 | Source totals equal harmonised totals plus logged corrections, per site and period; both planted data issues reported | Reconciliation table; data-quality report |
| 4 | Volume effect plus spend effect equals total variance on every row; the three planted events are flagged | Automated tests |
| 5 | No figure in any released commentary is missing from the context given to the model | Number-check log |
| 6 | Every dashboard figure equals the value in the variance table | Spot check of five values |
| 7 | All automated tests pass; a clean run from an empty database works with one command | Test report; run log |

## 8. Risk management

Risks are identified at planning, rated qualitatively and reviewed at every milestone. Details are in document 06.

## 9. Monitoring and controlling

| What is measured | How | When |
|---|---|---|
| Schedule | Actual versus planned milestone time | At each milestone |
| Scope | Number of requirements verified versus planned | At each milestone |
| Quality | Quality gate passed or failed; tests passing | End of each work package |
| Risk | Triggers in the risk register | At each milestone |
| Changes and decisions | Entries in document 07 | When they occur |

A short status entry is added to document 07 at each milestone, with a status of green, amber or red for schedule, scope and quality.

## 10. Configuration and tooling

| Item | Decision |
|---|---|
| Version control | Git, one repository, one commit per completed work package at minimum |
| Language | Python 3.11 or later |
| Database | DuckDB, one local file |
| Transformations | SQL files run against DuckDB |
| Analytics | pandas |
| Dashboard | Streamlit with Plotly charts |
| Language model | Accessed by API; provider and model set through environment variables; template fallback without a key |
| Tests | pytest |
| Low-code rebuild | KNIME Analytics Platform for the harmonisation step |
| Document storage | Folder docs/ in the repository |

## 11. Closing

The project closes when all success criteria are assessed, the closing report (document 08) is completed with lessons learned, the repository is tagged, and the demo has been rehearsed once.
