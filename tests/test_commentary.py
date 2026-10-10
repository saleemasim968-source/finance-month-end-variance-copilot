"""Quality gate for WBS 5, AI commentary (document 03 section 7).

No figure in any released commentary may be missing from the context given to the model
(FR-11 to FR-14, FR-16, NFR-04, NFR-05, SC-5). The model is replaced by a fake in these
tests, so no API is called.
"""

import json

import duckdb
import pytest

from src.commentary import context as context_builder
from src.commentary import llm, number_check
from src.commentary import run as commentary
from src.commentary.review import ReviewError, ReviewStore

TOOL_DOWN = "spend|FAB_NORTH|2026-05|Lithography|Maintenance"
WEAK_LOADING = "volume|FAB_ASIA|2026-07"


@pytest.fixture
def con(built):
    with duckdb.connect(str(built["db_path"]), read_only=True) as connection:
        yield connection


@pytest.fixture
def store(tmp_path):
    return ReviewStore(tmp_path / "review.duckdb")


@pytest.fixture
def log(tmp_path):
    return commentary.CommentaryLog(tmp_path / "llm_log.jsonl")


def tool_down_context(con, cause=None):
    return context_builder.build_context(con, TOOL_DOWN, cause)


def read_log(log):
    return [json.loads(line) for line in log.path.read_text(encoding="utf-8").splitlines()]


# --- Context (FR-11, NFR-04) -------------------------------------------------------------------

def test_context_holds_only_rounded_aggregated_figures(con):
    ctx = tool_down_context(con)
    assert ctx["figures"]["spend_effect_teur"] == 477
    assert ctx["figures"]["spend_effect_pct_of_flexed_budget"] == 156.9
    assert all(isinstance(v, int) for k, v in ctx["figures"].items() if k.endswith("_teur"))
    text = json.dumps(ctx)
    assert "source_file" not in text and "source_line" not in text


def test_every_flagged_item_has_a_context(con):
    items = [row[0] for row in con.execute("SELECT item_id FROM an_flagged_items").fetchall()]
    assert len(items) == 6
    for item_id in items:
        assert context_builder.build_context(con, item_id)["figures"]


# --- Number check (FR-12, SC-5) ----------------------------------------------------------------

def test_correct_draft_passes(con):
    ctx = tool_down_context(con)
    text = ("Lithography maintenance at FAB_NORTH (CC1010, account 440000) cost EUR 781k in May 2026, "
            "EUR +478k above the plan of EUR 303k. The spend effect is EUR 477k (156.9% of flexed budget).")
    assert number_check.check(text, ctx).passed


def test_draft_with_an_invented_number_fails(con):
    ctx = tool_down_context(con)
    result = number_check.check("The tool was down for 12 days and cost EUR 477k extra in May 2026.", ctx)
    assert not result.passed
    assert result.unknown_numbers == ["12"]


def test_derived_or_re_rounded_numbers_fail(con):
    ctx = tool_down_context(con)
    assert not number_check.check("Spend rose by EUR 0.48 million.", ctx).passed
    assert not number_check.check("Spend was 157% above budget.", ctx).passed


def test_period_labels_are_not_treated_as_figures(con):
    ctx = tool_down_context(con)
    for label in ("May 2026", "2026-05", "05.2026", "May-26", "Mai 2026"):
        assert number_check.check(f"In {label} the spend effect was EUR 477k.", ctx).passed, label


def test_numbers_in_the_owner_cause_are_allowed(con):
    ctx = tool_down_context(con, "Scanner tool-down for 6 days, emergency lens repair.")
    assert number_check.check("The tool was down for 6 days; spend effect EUR 477k.", ctx).passed


def test_german_number_format_is_understood(con):
    ctx = tool_down_context(con)
    assert number_check.check("Ausgabeneffekt EUR 477k (156,9 % des flexiblen Budgets).", ctx, "de").passed
    assert not number_check.check("Ausgabeneffekt EUR 477k (156,8 %).", ctx, "de").passed


# --- Template fallback (NFR-05, FR-16) ----------------------------------------------------------

@pytest.mark.parametrize("language", ["en", "de"])
def test_template_commentary_passes_the_check_for_every_item(con, language):
    for (item_id,) in con.execute("SELECT item_id FROM an_flagged_items").fetchall():
        ctx = context_builder.build_context(con, item_id, "Cause with 2 numbers: 3 shifts lost.")
        text = llm.template_text(ctx, language)
        assert number_check.check(text, ctx, language).passed, (item_id, language, text)


def test_without_a_key_the_template_is_used(monkeypatch, con):
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    draft = llm.generate(tool_down_context(con))
    assert draft.source == "template"
    assert number_check.check(draft.text, tool_down_context(con)).passed


def test_a_model_error_falls_back_to_the_template(monkeypatch, con):
    import anthropic

    def failing(prompt):
        raise anthropic.APIConnectionError(request=None)

    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_call_model", failing)
    draft = llm.generate(tool_down_context(con))
    assert draft.source == "template" and draft.error == "Network error"


# --- Regenerate once, then template (doc 04 §4.5, R01) ------------------------------------------

def test_a_good_model_draft_is_kept(monkeypatch, con, store, log):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_call_model", lambda prompt: "Spend effect of EUR 477k in May 2026.")
    row = commentary.draft_item(con, store, log, TOOL_DOWN)
    assert row["source"] == "llm" and row["check_passed"] and row["status"] == "Draft"


def test_invented_numbers_trigger_one_retry_then_the_template(monkeypatch, con, store, log):
    prompts = []

    def inventing(prompt):
        prompts.append(prompt)
        return "The repair took 9 days and cost EUR 999k."

    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_call_model", inventing)
    row = commentary.draft_item(con, store, log, TOOL_DOWN)

    assert len(prompts) == 2                                   # first try + one regeneration
    assert "rejected" in prompts[1]["user"] and "999" in prompts[1]["user"]
    assert row["source"] == "template" and row["check_passed"]
    events = [entry["event"] for entry in read_log(log)]
    assert events == ["draft", "draft", "fallback_to_template"]


def test_every_prompt_answer_and_check_is_logged(monkeypatch, con, store, log):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_call_model", lambda prompt: "Spend effect of EUR 477k.")
    commentary.draft_item(con, store, log, TOOL_DOWN)
    entry = read_log(log)[0]
    assert entry["prompt"]["system"] and '"spend_effect_teur": 477' in entry["prompt"]["user"]
    assert entry["answer"] == "Spend effect of EUR 477k."
    assert entry["check_passed"] is True and entry["unknown_numbers"] == []


# --- Review workflow (FR-13, FR-14) -------------------------------------------------------------

def test_draft_can_be_edited_rechecked_and_approved(con, store, log):
    commentary.draft_item(con, store, log, TOOL_DOWN)
    edited = store.edit(TOOL_DOWN, "Maintenance overspend of EUR 477k in May 2026 after a tool-down.")
    assert edited["source"] == "edited" and edited["check_passed"]

    approved = store.approve(TOOL_DOWN, "Manufacturing controller")
    assert approved["status"] == "Approved"
    assert approved["reviewer_role"] == "Manufacturing controller" and approved["approved_at"] is not None


def test_status_is_stored_and_survives_a_new_connection(con, store, log, tmp_path):
    commentary.draft_item(con, store, log, TOOL_DOWN)
    store.approve(TOOL_DOWN, "Cost-centre controller")
    assert ReviewStore(tmp_path / "review.duckdb").get(TOOL_DOWN)["status"] == "Approved"


def test_a_text_with_an_invented_number_cannot_be_approved(con, store, log):
    commentary.draft_item(con, store, log, TOOL_DOWN)
    store.edit(TOOL_DOWN, "Overspend of EUR 500k.")
    with pytest.raises(ReviewError, match="500"):
        store.approve(TOOL_DOWN, "Manufacturing controller")


def test_approved_text_is_locked_until_reopened(con, store, log):
    commentary.draft_item(con, store, log, TOOL_DOWN)
    store.approve(TOOL_DOWN, "Manufacturing controller")
    with pytest.raises(ReviewError):
        store.edit(TOOL_DOWN, "Changed after approval.")
    with pytest.raises(ReviewError):
        commentary.draft_item(con, store, log, TOOL_DOWN)
    assert store.reopen(TOOL_DOWN)["status"] == "Draft"


def test_owner_cause_appears_in_the_regenerated_draft(con, store, log):
    commentary.draft_item(con, store, log, WEAK_LOADING)
    store.set_cause(WEAK_LOADING, "Customer pushed out orders for automotive chips.")
    row = commentary.draft_item(con, store, log, WEAK_LOADING)
    assert "Customer pushed out orders for automotive chips." in row["text"]
    assert row["check_passed"]


def test_rerunning_the_pipeline_keeps_existing_commentary(built):
    from src.commentary.review import ReviewStore as Store
    store = Store(built["review_path"])
    before = store.all()
    assert len(before) == 6
    drafted = commentary.draft_all(built["db_path"], built["review_path"], built["log_path"])
    assert drafted == [] and store.all() == before
