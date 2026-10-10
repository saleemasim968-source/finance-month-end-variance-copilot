# Business case: Month-End Variance Copilot

*One page (WBS 7.4, BR-01, SC-8). Independent portfolio project; all data synthetic. **Every figure below is an estimate.** None has been measured in a real close; each must be validated with a practising controller (charter §9).*

## The process today and with the prototype

| Step at month-end | Today (manual) | With the prototype |
|---|---|---|
| Collect site reports | Three files in three layouts, languages, units and currencies | Same three files, loaded unchanged |
| Harmonise | Copy into one workbook; convert TEUR and MYR; re-key local accounts and cost centres | One command; maintained mapping tables; local codes kept beside group codes |
| Check | Spot checks by eye; duplicates and gaps found late, if at all | Duplicates, missing actuals and unmapped codes reported automatically; every site and month reconciled to source |
| Analyse | Plan versus actual; "volume or spending?" argued case by case | Flexed budget splits every variance into volume and spend effect; material items flagged by fixed thresholds |
| Explain | Controller writes all commentary from scratch | Draft from the calculated figures; every number checked; owner adds the cause; controller edits and approves |

## Estimated time per monthly close

| Activity | Today (h) | With prototype (h) | Assumption behind the estimate |
|---|---:|---:|---|
| Harmonise three site reports | 7.5 | 0.5 | 2.5 h per site today; afterwards one run plus reading the data-quality report |
| Data checks and reconciliation | 2.0 | 0.3 | Manual tie-out per site today; afterwards reviewing 54 automatic checks |
| Variance analysis and volume/spend split | 3.0 | 1.0 | Analysis remains, mechanics disappear |
| Commentary for material items | 6.0 | 1.5 | 6 items × 45 min + 1.5 h review loops today; 6 × 10 min review + 0.5 h for owner causes afterwards |
| **Total** | **18.5** | **3.3** | **About 15 hours saved per close; about 180 hours per year** |

At an assumed fully loaded cost of EUR 80 per controller hour, that is about **EUR 14,500 per year** for three sites, before any benefit from a shorter close. Cost of the prototype: open-source tools and less than EUR 5 of language-model use per month.

## Benefits that are not time

| Benefit | Measure | Prototype result (synthetic data) |
|---|---|---|
| Comparability | Sites on one account and cost-area structure | 3 of 3 sites, 648 of 648 rows mapped |
| Traceability | Reported figures with source file and line | 100 % of rows; every commentary figure checked against the data |
| Control | Planted data errors detected | 2 of 2 (one duplicate, one missing actual) |
| Focus | Planted business events flagged, no false alarms | 3 of 3 events; 6 flags in total, all explained by a planted event |

## Assumptions and how to validate them

1. **Hours today.** Time one real close: hours per site for harmonising, checking and commentary.
2. **Number of material items.** Run the thresholds (EUR 50k and 5 %) on one year of real data. Too many flags means raising them.
3. **Review effort afterwards.** Ask controllers to time the review of 10 drafts.
4. **Cost behaviour.** The variable shares (Energy 30 %, Materials 90 %, Maintenance 20 %) are illustrative. Agree real values with cost-centre owners; they live in one table.
5. **Data access.** A real roll-out needs authorised exports and a decision by IT security on sending aggregated figures to a language model. The prototype works without one.
