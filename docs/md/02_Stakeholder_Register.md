Month-End Variance Copilot

**Stakeholder Register**

| Document ID | VC-02 |
|---|---|
| Process group | Initiating |
| Version | 1.0 (baseline) |
| Date | 10 October 2026 |
| Project manager | Asim |
| Sponsor | Head of Frontend Cluster Finance (persona S01) |

Independent portfolio project. All data is synthetic and all stakeholders are assumed role personas. This is not a document of any real company and contains no internal or confidential information.

## 1. Purpose

This register identifies everyone who is affected by the project or can influence it, records what they expect, and sets how each one is engaged. The stakeholders are role personas that reflect a typical digital finance transformation in semiconductor manufacturing. No real person is named.

## 2. Stakeholder register

| ID | Group | Stakeholder | Main interest | Power | Interest | Current stance | Strategy | Engagement action | Req. source |
|---|---|---|---|---|---|---|---|---|---|
| S01 | Governance | Head of Frontend Cluster Finance (sponsor) | Faster close, comparable sites, visible results | High | High | Supportive | Manage closely | Demo at each milestone; one-page business case | Yes |
| S02 | Governance | Digital Finance Agenda lead | Reusable solutions that fit the long-term agenda | High | High | Supportive | Manage closely | Show reuse of the harmonisation layer; agree priorities | Yes |
| S03 | Finance users | Site finance heads (one per fab) | Local accuracy, own deadlines, local structures kept | High | Medium | Neutral to resistant | Keep satisfied | Keep local codes visible next to group codes; involve in mapping sign-off | Yes |
| S04 | Finance users | Cost-centre and manufacturing controllers | Less manual work at month-end; trust in the output | Medium | High | Neutral | Keep informed, involve in testing | They review and approve every commentary; collect feedback | Yes |
| S05 | Finance users | Cluster controlling and reporting | One consolidated view with identical definitions | High | High | Supportive | Manage closely | Agree the group chart of accounts and the variance method | Yes |
| S06 | Finance users | Accounting and closing team | Closing calendar, clean postings, master data | Medium | Medium | Neutral | Keep informed | No changes in the close window; share the data-quality report | Yes |
| S07 | Operations | Fab cost-centre owners (production, maintenance, facilities) | Their budgets; fair explanation of deviations | Medium | Medium | Neutral | Keep informed | Give them a simple field to enter the cause of a variance | Yes |
| S08 | Operations | Production planning | Correct use of wafer volume data | Low | Low | Neutral | Monitor | Confirm the volume definition once | No |
| S09 | IT and data | Finance IT and ERP process owners | System stability, authorised interfaces | High | Low | Neutral | Keep satisfied | File-based prototype only; no system access requested | No |
| S10 | IT and data | Data platform and master-data governance | Standards, one source of truth, no shadow tools | Medium | Medium | Sceptical | Keep satisfied | SQL-based logic that can move to the platform; mappings as governed tables | Yes |
| S11 | Control | IT security and AI governance | What financial data may be sent to a language model | High | Medium | Sceptical | Keep satisfied | Aggregated figures only; prompts and answers logged | Yes |
| S12 | Control | Internal controls and audit | Traceability and reproducibility of reported numbers | High | Medium | Neutral | Keep satisfied | Lineage, number check, human sign-off, automated tests | Yes |
| S13 | Control | Works council and data protection | No monitoring of individuals; protection of personnel data | High | Low | Neutral | Keep satisfied | Cost-centre level only; no person-level data anywhere | Yes |
| S14 | Peers | Other digitalisation teams | Reuse, no duplicate solutions | Low | Medium | Supportive | Keep informed | Share the README and the mapping approach | No |

## 3. Power and interest grid

| Quadrant | Stakeholders | Approach |
|---|---|---|
| High power, high interest: manage closely | S01, S02, S05 | Involve in decisions; demo at every milestone |
| High power, lower interest: keep satisfied | S03, S09, S11, S12, S13 | Meet their conditions early; no surprises |
| Lower power, high interest: keep informed | S04, S07, S10, S14, S06 | Regular updates; use them as testers and reviewers |
| Lower power, lower interest: monitor | S08 | Contact only when volume data is concerned |

## 4. Conflicts between stakeholders and how the project resolves them

| No. | Conflict | Parties | Resolution in this project | Requirement |
|---|---|---|---|---|
| C1 | One group standard versus keeping local account structures | S05, S10 versus S03 | Reporting uses the group chart of accounts, and every row keeps its local account and cost-centre code so sites can still recognise their data | FR-04, FR-05 |
| C2 | Speed of AI-written commentary versus control over reported numbers | S01, S04 versus S11, S12 | The model only words figures that the pipeline calculated; an automatic check blocks any other number; a controller approves each text | FR-11, FR-12, FR-13 |
| C3 | Detailed cost transparency versus protection of employees | S01, S05 versus S13 | Personnel cost is reported at cost-centre level only | NFR-01 |
| C4 | Quick local prototype versus platform standards | S01, S02 versus S09, S10 | Transformations are written in SQL and mappings are tables, so the logic can be moved to the central platform later | NFR-06 |
| C5 | Finance explains variances, but operations know the causes | S04 versus S07 | Cost-centre owners can enter a short cause, which the commentary must use | FR-14 |

## 5. Communication summary

| Audience | Information | Format | Frequency |
|---|---|---|---|
| S01, S02 | Status against milestones, risks, decisions needed | Short status note and live demo | At each milestone |
| S03, S04, S05 | Mapping tables, variance method, commentary samples | Review session | Once per work package |
| S11, S12, S13 | Data used, AI controls, test evidence | Written summary | Before commentary goes live |
| S06, S07, S08, S09, S10, S14 | What changes for them | Information note | At project close |
