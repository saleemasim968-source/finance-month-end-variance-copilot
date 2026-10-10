Month-End Variance Copilot

**Risk Register**

| Document ID | VC-06 |
|---|---|
| Process group | Planning; Monitoring and Controlling |
| Version | 1.0 (baseline) |
| Date | 10 October 2026 |
| Project manager | Asim |
| Sponsor | Head of Frontend Cluster Finance (persona S01) |

Independent portfolio project. All data is synthetic and all stakeholders are assumed role personas. This is not a document of any real company and contains no internal or confidential information.

## 1. Purpose and method

This register lists the identified risks, their rating and the planned response. Probability and impact are rated Low, Medium or High. The overall rating follows the matrix in section 3. The project manager owns all risks and reviews the register at every milestone.

## 2. Risk register

| ID | Type | Risk | Cause | Prob. | Impact | Rating | Strategy | Response | Trigger |
|---|---|---|---|---|---|---|---|---|---|
| R01 | Threat | The language model states a figure that is not in the variance table | Models can invent or miscalculate numbers | Medium | High | High | Mitigate | Give the model only calculated figures; automatic number check rejects any other value; controller approval before release | Number check rejects a draft |
| R02 | Threat | Documentation or extra features use up the build time | Fixed weekend duration | High | High | High | Mitigate | Documentation capped at three hours; MoSCoW priorities; "Could" items dropped first | A milestone slips by more than one hour |
| R03 | Threat | A wrong account, unit or currency mapping produces wrong consolidated numbers | Three different source layouts | Medium | High | High | Mitigate | Reconciliation of every site and period against source totals; unmapped codes stop the run | Reconciliation difference above 0.01% |
| R04 | Threat | The project manager cannot explain code written by the AI assistant | Agent-led build | Medium | High | High | Mitigate | Build one work package at a time; read each file; assistant writes a plain-language explanation per module | A module cannot be explained in two sentences |
| R05 | Threat | Internal or confidential information enters the repository | Project manager works in the industry | Low | High | Medium | Avoid | Synthetic data and public knowledge only; fictional site names; notice on every document and screen | Any real name or figure appears |
| R06 | Threat | Language model service is unavailable or slow during the demo | Dependency on an external service | Medium | Medium | Medium | Mitigate | Template-based fallback commentary; store generated drafts so the demo can run offline | API call fails or takes over 20 seconds |
| R07 | Threat | The assumed fixed and variable cost split is challenged | Cost behaviour is an assumption | Medium | Medium | Medium | Accept, with transparency | Keep the split in a reference table that the user can change; state it on the dashboard | Reviewer questions the volume effect |
| R08 | Threat | The live demo fails on the day | Local environment issues | Low | High | Medium | Mitigate | Pinned package versions; rehearsal; screenshots and a short recording as backup | Rehearsal shows an error |
| R09 | Threat | The synthetic data looks unrealistic to finance experts | No access to real cost structures | Medium | Medium | Medium | Accept, with transparency | Present the data as illustrative; focus on method; ask a practising controller for feedback | Feedback from a reviewer |
| R10 | Threat | False variance flags caused by random noise reduce trust | Thresholds set too low | Low | Medium | Low | Mitigate | Two-part threshold (percentage and amount); thresholds configurable | More than five flags without a business cause |
| R11 | Opportunity | The harmonisation layer can be reused for other finance use cases | Mappings and staging are generic | Medium | Medium | Medium | Exploit | Keep mappings as separate tables; describe reuse in the closing report | Sponsor asks for a follow-up use case |

## 3. Rating matrix

| Probability | Impact Low | Impact Medium | Impact High |
|---|---|---|---|
| High | Medium | High | High |
| Medium | Low | Medium | High |
| Low | Low | Low | Medium |

## 4. Review

New risks and changes of rating are recorded here with the date. Risks that occur become issues and are recorded in document 07.
