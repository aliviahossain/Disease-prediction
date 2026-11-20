"""
Prediction history for the Streamlit analytics dashboard.

Entries are stored in the app's dedicated database (see backend/storage.py),
in the ``dashboard_history`` table, alongside users and per-user history.
The Streamlit dashboard runs outside the Flask app, so this module talks to
the database through its own lightweight SQLAlchemy engine.

Earlier versions kept these entries in a JSON file at
``~/.disease_prediction/prediction_history.json``; that file is imported
once automatically and then renamed to ``*.imported``.
"""

import json
import os
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    delete,
    func,
    insert,
    select,
)

from backend.storage import get_database_uri

_metadata = MetaData()

dashboard_history = Table(
    "dashboard_history",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("entry", Text, nullable=False),  # JSON-encoded entry dict
)

_engine = None
_engine_uri = None

_LEGACY_JSON = os.path.join(
    os.environ.get(
        "HISTORY_DATA_DIR",
        os.path.join(os.path.expanduser("~"), ".disease_prediction"),
    ),
    "prediction_history.json",
)


def _get_engine():
    """Create (or reuse) the engine; re-create it if the database URI changed."""
    global _engine, _engine_uri
    uri = get_database_uri()
    if _engine is None or uri != _engine_uri:
        _engine = create_engine(uri, pool_pre_ping=True)
        _engine_uri = uri
        _metadata.create_all(_engine)
        _import_legacy_json(_engine)
    return _engine


def _import_legacy_json(engine):
    """One-time import of the old JSON history file into the database."""
    if not os.path.exists(_LEGACY_JSON):
        return
    try:
        with open(_LEGACY_JSON, encoding="utf-8") as f:
            entries = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    if entries:
        with engine.begin() as conn:
            conn.execute(
                insert(dashboard_history),
                [
                    {"created_at": datetime.utcnow(), "entry": json.dumps(e)}
                    for e in entries
                ],
            )
    try:
        os.replace(_LEGACY_JSON, _LEGACY_JSON + ".imported")
    except OSError:
        pass
    print(f"[OK] Imported {len(entries)} dashboard history entries into the database")


def load_history():
    """Return all dashboard history entries (oldest first) as dicts."""
    with _get_engine().connect() as conn:
        rows = conn.execute(
            select(dashboard_history.c.entry).order_by(dashboard_history.c.id)
        ).scalars()
        return [json.loads(row) for row in rows]


def save_history(entry):
    """Append one entry (a JSON-serialisable dict)."""
    with _get_engine().begin() as conn:
        conn.execute(
            insert(dashboard_history).values(
                created_at=datetime.utcnow(), entry=json.dumps(entry, default=str)
            )
        )


def clear_history():
    """Delete all dashboard history entries."""
    with _get_engine().begin() as conn:
        conn.execute(delete(dashboard_history))


def get_total_predictions():
    with _get_engine().connect() as conn:
        return conn.execute(
            select(func.count()).select_from(dashboard_history)
        ).scalar_one()


def get_risk_distribution():
    risk_counts = {"Low": 0, "Moderate": 0, "High": 0}
    for entry in load_history():
        risk = entry.get("Risk")
        if risk in risk_counts:
            risk_counts[risk] += 1
    return risk_counts
