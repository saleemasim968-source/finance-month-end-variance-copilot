"""Review workflow (WBS 5.4, FR-13, FR-14, D-008, D-019).

Stores each commentary with its status (Draft or Approved), the reviewer role and approval
time, and the cause entered by the cost-centre owner. The store is a separate DuckDB file
(data/review/review.duckdb) that the pipeline never rebuilds, so approvals survive reruns.

Rules:
- A text can be edited only while it is a Draft. Every edit is number-checked again.
- Only a Draft that passes the number check can be approved (no unchecked figure is released).
- Reopening an approved text sets it back to Draft.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from src.commentary import number_check

SCHEMA = """
CREATE TABLE IF NOT EXISTS cm_commentary (
    item_id         VARCHAR PRIMARY KEY,
    language        VARCHAR NOT NULL,
    text            VARCHAR NOT NULL,
    source          VARCHAR NOT NULL,      -- llm, template or edited
    model           VARCHAR,
    check_passed    BOOLEAN NOT NULL,
    unknown_numbers VARCHAR,
    context_json    VARCHAR NOT NULL,
    status          VARCHAR NOT NULL,      -- Draft or Approved
    generated_at    TIMESTAMP NOT NULL,
    edited_at       TIMESTAMP,
    reviewer_role   VARCHAR,
    approved_at     TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cm_owner_cause (
    item_id          VARCHAR PRIMARY KEY,
    cause            VARCHAR NOT NULL,
    entered_by_role  VARCHAR NOT NULL,
    entered_at       TIMESTAMP NOT NULL
);
"""


class ReviewError(Exception):
    """An action that the review rules do not allow."""


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


class ReviewStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute(SCHEMA)

    def _connect(self):
        return duckdb.connect(str(self.path))

    def _rows(self, sql, params=()):
        with self._connect() as con:
            cursor = con.execute(sql, params)
            columns = [d[0] for d in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # --- Reading --------------------------------------------------------------------------

    def get(self, item_id):
        rows = self._rows("SELECT * FROM cm_commentary WHERE item_id = ?", [item_id])
        return rows[0] if rows else None

    def all(self):
        return {row["item_id"]: row for row in self._rows("SELECT * FROM cm_commentary")}

    def get_cause(self, item_id):
        rows = self._rows("SELECT * FROM cm_owner_cause WHERE item_id = ?", [item_id])
        return rows[0] if rows else None

    def all_causes(self):
        return {row["item_id"]: row for row in self._rows("SELECT * FROM cm_owner_cause")}

    # --- Writing --------------------------------------------------------------------------

    def save_draft(self, item_id, text, source, model, context, language, result):
        """Store a newly generated draft. Replaces an existing text unless it is approved."""
        existing = self.get(item_id)
        if existing and existing["status"] == "Approved":
            raise ReviewError(f"{item_id} is approved. Reopen it before regenerating.")
        with self._connect() as con:
            con.execute("""
                INSERT OR REPLACE INTO cm_commentary
                (item_id, language, text, source, model, check_passed, unknown_numbers, context_json,
                 status, generated_at, edited_at, reviewer_role, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Draft', ?, NULL, NULL, NULL)
            """, [item_id, language, text, source, model, result.passed, ", ".join(result.unknown_numbers),
                  json.dumps(context, ensure_ascii=False), _now()])
        return self.get(item_id)

    def edit(self, item_id, text):
        """Change the text of a Draft. The edit is number-checked against the stored context."""
        row = self._require(item_id)
        if row["status"] != "Draft":
            raise ReviewError(f"{item_id} is approved and cannot be edited. Reopen it first.")
        result = number_check.check(text, json.loads(row["context_json"]), row["language"])
        with self._connect() as con:
            con.execute("""
                UPDATE cm_commentary
                SET text = ?, source = 'edited', check_passed = ?, unknown_numbers = ?, edited_at = ?
                WHERE item_id = ?
            """, [text, result.passed, ", ".join(result.unknown_numbers), _now(), item_id])
        return self.get(item_id)

    def approve(self, item_id, reviewer_role):
        row = self._require(item_id)
        if not reviewer_role or not reviewer_role.strip():
            raise ReviewError("A reviewer role is required to approve.")
        if row["status"] == "Approved":
            raise ReviewError(f"{item_id} is already approved.")
        if not row["check_passed"]:
            raise ReviewError(f"{item_id} contains figures not in the data ({row['unknown_numbers']}). "
                              "Edit or regenerate it before approval.")
        with self._connect() as con:
            con.execute("""
                UPDATE cm_commentary SET status = 'Approved', reviewer_role = ?, approved_at = ?
                WHERE item_id = ?
            """, [reviewer_role.strip(), _now(), item_id])
        return self.get(item_id)

    def reopen(self, item_id):
        self._require(item_id)
        with self._connect() as con:
            con.execute("""
                UPDATE cm_commentary SET status = 'Draft', reviewer_role = NULL, approved_at = NULL
                WHERE item_id = ?
            """, [item_id])
        return self.get(item_id)

    def set_cause(self, item_id, cause, entered_by_role="Cost-centre owner"):
        cause = (cause or "").strip()
        if not cause:
            raise ReviewError("The cause must not be empty.")
        if len(cause) > 300:
            raise ReviewError("Keep the cause short (300 characters at most).")
        with self._connect() as con:
            con.execute("INSERT OR REPLACE INTO cm_owner_cause VALUES (?, ?, ?, ?)",
                        [item_id, cause, entered_by_role, _now()])
        return self.get_cause(item_id)

    def _require(self, item_id):
        row = self.get(item_id)
        if row is None:
            raise ReviewError(f"No commentary for {item_id}.")
        return row
