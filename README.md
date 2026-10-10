# Finance Month-End Variance Copilot

> **Independent portfolio project. All data is synthetic, and all sites and stakeholders are fictional. This is not the work of any real company and contains no internal or confidential information.**

A local prototype that takes month-end cost reports from three fictional wafer fabs, each in a different layout, currency and account structure, and:

1. **harmonises** them into one reporting table (group chart of accounts, EUR, YYYY-MM), keeping the local codes and source lineage;
2. **checks** data quality and reconciles to the source totals;
3. **analyses** plan-versus-actual variances, split into a volume effect and a spend effect using a flexed budget;
4. **explains** material variances with AI-drafted commentary. Every figure is checked automatically, and a controller approves each text.

**Status:** planning complete, build in progress. The specification is in [`docs/`](docs/), and the design is in [`docs/architecture.md`](docs/architecture.md).

**Stack:** Python, DuckDB (SQL), pandas, Streamlit + Plotly, pytest, KNIME.

Setup and demo instructions will follow (WBS 7.3).
