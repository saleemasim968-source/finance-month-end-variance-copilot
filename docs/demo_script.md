# Demo script: three minutes

*Independent portfolio project; all data synthetic. Before the demo: `python -m src.pipeline.run`, then `python -m app.backend`, and open http://127.0.0.1:8000. Reset approvals beforehand by deleting `data/review/review.duckdb` and rerunning the pipeline. Fallback if anything fails: the screenshots in `docs/screenshots/` (R08).*

| Time | Screen | Say | Do |
|---|---|---|---|
| 0:00 | Overview | "Three fabs send month-end costs in three layouts: English in euros, German in thousands of euros with decimal commas, a Malaysian ledger export in ringgit. Today a controller merges and explains them by hand." | Point at the synthetic-data notice. |
| 0:20 | Overview | "One command loads, harmonises, checks and analyses everything. It takes about a second. Variance is split into a volume effect, from producing fewer or more wafers, and a spend effect, from spending more than the flexed budget." | Point at the monthly chart: May spike, the Jul–Sep blue volume bars. |
| 0:50 | Data quality | "Nothing is edited by hand. The pipeline found the two errors in the source files, a duplicate line and a missing actual, and shows the exact file and line. Every site and month reconciles to the source, to the cent." | Show the findings and the 54 passes. |
| 1:15 | Variance bridge | "The bridge for North in May: almost all of the variance is maintenance spending. Every row links back to its source line." | Select FAB_NORTH and May 2026. Scroll to the flagged row. |
| 1:40 | Flagged items | "Six items crossed the thresholds, exactly the three planted events. The draft is written from the calculated figures only." | Open the North maintenance item. |
| 2:00 | Flagged items | "The cost-centre owner adds the cause; the draft is regenerated with it." | Type "Scanner tool-down, emergency lens repair." → Save cause → Regenerate. |
| 2:20 | Flagged items | "If anyone types a figure that isn't in the data, the check catches it and approval is blocked." | Change 477 to 500 → Save edit → red "Unverified figures", Approve disabled. Change it back → Save edit. |
| 2:40 | Flagged items | "A controller approves; the role and time are recorded. The AI drafts, the pipeline owns the numbers, and a person signs off." | Choose "Manufacturing controller" → Approve. |
| 2:55 | — | "Business case: about 15 hours saved per close, as an estimate to validate with a practising controller." | End. |
