"""Backend API for the prototype (WBS 6, FR-15, change C-005).

A small FastAPI app. It serves the frontend (app/frontend/) and a JSON API over the
warehouse and the review store:

  GET  /api/meta                       notice, sites, periods, thresholds, writer
  GET  /api/overview?period=           KPI totals, monthly effects, sites
  GET  /api/sites?period=              cost per wafer, trend, variance % by site and account
  GET  /api/bridge?site=&period=       plan -> volume -> spend by account -> actual, with rows
  GET  /api/flags                      flagged items with figures, commentary and cause
  POST /api/flags/{id}/regenerate      new draft (template or Claude), number-checked
  PUT  /api/flags/{id}/text            edit a draft (re-checked)
  POST /api/flags/{id}/approve         approve with reviewer role
  POST /api/flags/{id}/reopen          back to Draft
  PUT  /api/flags/{id}/cause           cost-centre owner's cause
  GET  /api/data-quality               findings, reconciliation, mapping coverage
  POST /api/pipeline/run               rebuild everything from the raw files

Run: python -m app.backend   (then open http://127.0.0.1:8000)
"""

import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import duckdb
import plotly
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.backend import queries
from src.commentary import context as context_builder
from src.commentary import llm
from src.commentary import run as commentary
from src.commentary.review import ReviewError, ReviewStore
from src.pipeline import run as pipeline
from src.pipeline.quality import ReconciliationError, UnmappedCodesError

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "app" / "frontend"
PLOTLY_JS = Path(plotly.__file__).parent / "package_data" / "plotly.min.js"

NOTICE = ("Independent portfolio project. All data is synthetic, and all sites and stakeholders are "
          "fictional. Not the work of any real company; no internal or confidential information.")
REVIEWER_ROLES = ["Cost-centre controller", "Manufacturing controller", "Cluster controlling"]

# One lock for all warehouse and review access: a single-user prototype, and DuckDB must not
# be read while the pipeline rebuilds the file.
LOCK = threading.RLock()


class Settings:
    def __init__(self, warehouse_path=None, review_path=None, log_path=None):
        config = pipeline.load_config()
        self.config = config
        self.warehouse_path = Path(warehouse_path or ROOT / config["warehouse_path"])
        self.review_path = Path(review_path or ROOT / config["commentary"]["review_path"])
        self.log_path = Path(log_path or ROOT / config["commentary"]["log_path"])


settings = Settings()


def configure(**paths):
    """Point the app at other files (used by tests)."""
    global settings
    settings = Settings(**paths)


@contextmanager
def warehouse():
    if not settings.warehouse_path.exists():
        raise HTTPException(503, "No data yet. Run the pipeline first: python -m src.pipeline.run")
    with LOCK, duckdb.connect(str(settings.warehouse_path), read_only=True) as con:
        yield con


def review_store():
    return ReviewStore(settings.review_path)


app = FastAPI(title="Finance Month-End Variance Copilot", version="1.0")


# --- Read endpoints ----------------------------------------------------------------------------

@app.get("/api/meta")
def get_meta():
    with warehouse() as con:
        data = queries.meta(con)
    return {
        **data,
        "notice": NOTICE,
        "materiality": settings.config["materiality"],
        "commentary_language": settings.config["commentary"]["language"],
        "writer": llm.provider(),
        "model": llm.model_name() if llm.provider() == "anthropic" else None,
        "reviewer_roles": REVIEWER_ROLES,
        "data_refreshed_at": datetime.fromtimestamp(settings.warehouse_path.stat().st_mtime)
                                     .isoformat(timespec="seconds"),
    }


@app.get("/api/overview")
def get_overview(period: str = "all"):
    with warehouse() as con:
        return queries.overview(con, period)


@app.get("/api/sites")
def get_sites(period: str = "all"):
    with warehouse() as con:
        return queries.sites(con, period)


@app.get("/api/bridge")
def get_bridge(site: str = "all", period: str = "all"):
    with warehouse() as con:
        return queries.bridge(con, site, period)


@app.get("/api/data-quality")
def get_data_quality():
    with warehouse() as con:
        return queries.data_quality(con)


@app.get("/api/flags")
def get_flags():
    with warehouse() as con:
        store = review_store()
        texts, causes = store.all(), store.all_causes()
        items = []
        for item in queries.flagged_items(con):
            item_id = item["item_id"]
            cause = causes.get(item_id)
            ctx = context_builder.build_context(con, item_id, cause["cause"] if cause else None)
            items.append({**item, "figures": ctx["figures"],
                          "local_cost_centre": ctx.get("local_cost_centre"),
                          "local_account_code": ctx.get("local_account_code"),
                          "commentary": _public(texts.get(item_id)), "cause": cause})
    return items


def _public(row):
    if row is None:
        return None
    return {k: v for k, v in row.items() if k != "context_json"}


# --- Review actions ----------------------------------------------------------------------------

class TextBody(BaseModel):
    text: str


class ApproveBody(BaseModel):
    reviewer_role: str


class CauseBody(BaseModel):
    cause: str


class RegenerateBody(BaseModel):
    language: str | None = None


def _review_action(action):
    try:
        with LOCK:
            return _public(action())
    except ReviewError as error:
        raise HTTPException(409, str(error)) from error


@app.post("/api/flags/{item_id}/regenerate")
def regenerate(item_id: str, body: RegenerateBody | None = None):
    language = (body.language if body and body.language else None) or settings.config["commentary"]["language"]
    if language not in ("en", "de"):
        raise HTTPException(422, "language must be en or de")
    with warehouse() as con:
        store = review_store()
        log = commentary.CommentaryLog(settings.log_path)
        try:
            return _public(commentary.draft_item(con, store, log, item_id, language))
        except KeyError as error:
            raise HTTPException(404, f"Unknown item {item_id}") from error
        except ReviewError as error:
            raise HTTPException(409, str(error)) from error


@app.put("/api/flags/{item_id}/text")
def edit_text(item_id: str, body: TextBody):
    return _review_action(lambda: review_store().edit(item_id, body.text))


@app.post("/api/flags/{item_id}/approve")
def approve(item_id: str, body: ApproveBody):
    return _review_action(lambda: review_store().approve(item_id, body.reviewer_role))


@app.post("/api/flags/{item_id}/reopen")
def reopen(item_id: str):
    return _review_action(lambda: review_store().reopen(item_id))


@app.put("/api/flags/{item_id}/cause")
def set_cause(item_id: str, body: CauseBody):
    try:
        with LOCK:
            return review_store().set_cause(item_id, body.cause)
    except ReviewError as error:
        raise HTTPException(409, str(error)) from error


# --- Pipeline ----------------------------------------------------------------------------------

@app.post("/api/pipeline/run")
def run_pipeline():
    try:
        with LOCK:
            summary = pipeline.run(db_path=settings.warehouse_path, review_path=settings.review_path,
                                   log_path=settings.log_path)
    except (UnmappedCodesError, ReconciliationError) as error:
        raise HTTPException(422, str(error)) from error
    summary["db_path"] = str(summary["db_path"])
    return summary


# --- Frontend ----------------------------------------------------------------------------------

@app.get("/vendor/plotly.min.js", include_in_schema=False)
def plotly_js():
    return FileResponse(PLOTLY_JS, media_type="text/javascript")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
