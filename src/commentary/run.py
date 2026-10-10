"""Draft commentary for flagged items (WBS 5): context -> model or template -> number check -> store.

Each draft that fails the number check is regenerated once with feedback; if it fails again,
the template text is used (doc 04 §4.5). Every prompt, answer and check result is appended
to logs/llm_log.jsonl (NFR-04). Existing commentary is kept unless regeneration is asked for
(D-017), so a rerun of the pipeline does not change approved texts.

Usage: python -m src.commentary.run [--regenerate] [--language de]
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from src.commentary import context as context_builder
from src.commentary import llm, number_check
from src.commentary.review import ReviewStore

ROOT = Path(__file__).resolve().parents[2]


class CommentaryLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, item_id, event, **fields):
        record = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "item_id": item_id, "event": event, **fields}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def draft_item(con, store, log, item_id, language="en"):
    """Generate, check and store one draft. Returns the stored row."""
    cause_row = store.get_cause(item_id)
    context = context_builder.build_context(con, item_id, cause_row["cause"] if cause_row else None)

    feedback = None
    for attempt in (1, 2):
        draft = llm.generate(context, language, feedback)
        result = number_check.check(draft.text, context, language)
        log.write(item_id, "draft", attempt=attempt, source=draft.source, model=draft.model,
                  prompt=draft.prompt, answer=draft.text, error=draft.error,
                  check_passed=result.passed, unknown_numbers=result.unknown_numbers)
        if result.passed or draft.source == "template":
            break
        feedback = f"it contained numbers that are not in the data: {', '.join(result.unknown_numbers)}."

    if not result.passed:  # second model draft failed too: use the template (always checkable)
        text = llm.template_text(context, language)
        result = number_check.check(text, context, language)
        draft = llm.Draft(text, "template", None, None, error="model drafts failed the number check")
        log.write(item_id, "fallback_to_template", answer=text, check_passed=result.passed,
                  unknown_numbers=result.unknown_numbers)

    return store.save_draft(item_id, draft.text, draft.source, draft.model, context, language, result)


def draft_all(warehouse_path, review_path, log_path, language="en", regenerate=False):
    """Draft every flagged item that has no commentary yet (or every Draft, if regenerate)."""
    store = ReviewStore(review_path)
    log = CommentaryLog(log_path)
    existing = store.all()
    drafted = []
    with duckdb.connect(str(warehouse_path), read_only=True) as con:
        item_ids = [row[0] for row in con.execute("SELECT item_id FROM an_flagged_items ORDER BY item_id").fetchall()]
        for item_id in item_ids:
            current = existing.get(item_id)
            if current and (not regenerate or current["status"] == "Approved"):
                continue
            drafted.append(draft_item(con, store, log, item_id, language))
    return drafted


def main():
    from src.commentary.llm import load_env_file
    load_env_file()
    from src.pipeline.run import load_config

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--regenerate", action="store_true", help="redraft all items still in Draft")
    parser.add_argument("--language", choices=["en", "de"], default=None)
    args = parser.parse_args()

    config = load_config()
    paths = config["commentary"]
    drafted = draft_all(ROOT / config["warehouse_path"], ROOT / paths["review_path"], ROOT / paths["log_path"],
                        args.language or paths["language"], args.regenerate)
    for row in drafted:
        print(f"{row['item_id']:<50} {row['source']:<9} check {'passed' if row['check_passed'] else 'FAILED'}")
    print(f"{len(drafted)} draft(s) written. Writer: {llm.provider()}")


if __name__ == "__main__":
    main()
