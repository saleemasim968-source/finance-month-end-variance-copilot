Month-End Variance Copilot

**Project Charter**

| Document ID | VC-01 |
|---|---|
| Process group | Initiating |
| Version | 1.0 (baseline) |
| Date | 10 October 2026 |
| Project manager | Asim |
| Sponsor | Head of Frontend Cluster Finance (persona S01) |

Independent portfolio project. All data is synthetic and all stakeholders are assumed role personas. This is not a document of any real company and contains no internal or confidential information.

## 1. Purpose of this charter

This charter formally authorises the Month-End Variance Copilot project, names the project manager, and records the business need, objectives, boundaries and success criteria agreed with the sponsor.

## 2. Background and business need

The frontend finance organisation in this scenario runs three wafer fabs: FAB_NORTH, FAB_ALPS and FAB_ASIA. At every month-end, each site exports its cost-centre report in its own layout, language, currency and account structure. Controllers then consolidate the files by hand and write the plan-versus-actual commentary manually.

This causes three problems:

- **Slow close:** harmonising and explaining variances takes controller time in the most time-critical days of the month.

- **Low comparability:** sites cannot be compared directly because accounts, cost centres and units differ.

- **Low transparency:** commentary does not separate "we produced less" from "we spent more", and the figures in the text are not traceable to source.

## 3. Project objective

Deliver a working prototype that takes the three site reports, harmonises them into one reporting table, calculates and decomposes cost variances, flags the material ones, and drafts commentary that a controller reviews and approves.

## 4. Measurable success criteria

| ID | Criterion | Target |
|---|---|---|
| SC-1 | Rows mapped to the group chart of accounts and group cost areas | 100% of source rows |
| SC-2 | Harmonised totals reconcile to source totals per site and period (in EUR, at the reference FX rate) | Difference below 0.01% |
| SC-3 | Planted data-quality issues detected (one missing actual, one duplicate line) | 2 of 2 |
| SC-4 | Planted business events appear in the flagged list (tool-down, energy spike, weak loading) | 3 of 3 |
| SC-5 | Figures in released commentary that are traceable to the variance table | 100%, zero unverified figures |
| SC-6 | End-to-end run from raw files to dashboard data with one command | Under 2 minutes |
| SC-7 | Automated tests for transformation and variance logic | All passing |
| SC-8 | Time-saving estimate documented with explicit assumptions | One-page business case delivered |

## 5. High-level scope

### In scope

- Synthetic month-end cost data for three sites, January to September 2026

- ELT pipeline with raw, staging and harmonised layers

- Data-quality checks and source reconciliation

- Variance analysis with volume and spend effects, and cost per wafer

- AI-drafted commentary with an automatic number check and a human approval step

- Dashboard, automated tests, KNIME rebuild of the harmonisation step, and a business case

### Out of scope

- Any real company data, system or interface

- ERP integration, user authentication and production deployment

- Forecasting, accruals, intercompany and balance-sheet topics

- Any person-level data

## 6. Key deliverables

| No. | Deliverable | Acceptance evidence |
|---|---|---|
| D1 | Project documentation set (documents 01 to 08) | Baselined and stored in the repository |
| D2 | Synthetic data set and reference tables | Files present, row counts as specified in document 04 |
| D3 | ELT pipeline and harmonised reporting table | SC-1, SC-2, SC-6 |
| D4 | Data-quality report | SC-3 |
| D5 | Variance engine | SC-4, SC-7 |
| D6 | AI commentary module with number check and review status | SC-5 |
| D7 | Dashboard | Walk-through against requirements FR-15 |
| D8 | KNIME workflow, README, demo script, business case | SC-8 |

## 7. Summary milestones

| ID | Milestone | Target |
|---|---|---|
| M1 | Documentation baselined | Sat 10 Oct, 16:30 |
| M2 | Harmonised table reconciled | Sat 10 Oct, 20:00 |
| M3 | Variance engine tested | Sun 11 Oct, 11:00 |
| M4 | Commentary with number check working | Sun 11 Oct, 13:30 |
| M5 | Dashboard complete | Sun 11 Oct, 16:30 |
| M6 | Project closed, demo rehearsed | Sun 11 Oct, 19:30 |

## 8. Budget and resources

- **Team:** one person acting as project manager and developer, supported by an AI coding assistant.

- **Effort:** about 16 working hours over one weekend.

- **Cost:** open-source tools only. LLM usage is expected to stay below EUR 5.

## 9. Assumptions and constraints

- **Assumption:** the synthetic data is realistic enough to demonstrate the method. The cost structure is illustrative, not benchmarked.

- **Assumption:** the time-saving figures in the business case are estimates to be validated with a practising controller.

- **Constraint:** only synthetic data and public information may be used.

- **Constraint:** fixed duration of one weekend. Scope is the variable, not time.

- **Constraint:** the solution must run on one laptop without paid infrastructure.

## 10. High-level risks

- The language model states figures that are not in the data.

- Documentation or extra features consume the time needed for the build.

- A mapping error produces wrong consolidated numbers.

- The project manager cannot explain code written by the AI assistant.

The full list with responses is in document 06, Risk Register.

## 11. Authority of the project manager

The project manager may decide on tools, design and the order of work, and may remove "Should" and "Could" requirements to protect the schedule. Changes to "Must" requirements or to the success criteria need sponsor approval and an entry in document 07.

## 12. Approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Sponsor | Head of Frontend Cluster Finance (persona S01) | Approved (simulated) | 10 Oct 2026 |
| Project manager | Asim | Accepted | 10 Oct 2026 |
