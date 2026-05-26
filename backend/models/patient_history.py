"""
PatientHistory model.

Stores a record of every disease-probability calculation or ML prediction
performed by an authenticated user, so it can be shown back to them on the
History page.

This file fixes issue #230 — predictions were never persisted, so the
History page had nothing to display.
"""

from datetime import datetime

from backend import \
    db  # the SQLAlchemy() instance created in backend/__init__.py


class PatientHistory(db.Model):
    """A single saved prediction / calculation entry for a user.

    One row is created per call to the Bayesian calculator or the
    image-based disease-type predictor, provided the user is logged in.
    """

    __tablename__ = "patient_history"

    id = db.Column(db.Integer, primary_key=True)

    # FK to the User model. The repo's User table is named "user"
    # (singular) — confirmed by backend/__init__.py's
    # `_ensure_user_profile_columns` helper, which inspects the "user"
    # table directly.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # What kind of prediction was this — used by the UI for grouping/icons
    # 'bayes'      → Bayes-theorem calculator
    # 'eye'        → eye-disease image classifier
    # 'skin'       → skin-disease image classifier
    # 'symptom'    → symptom-based ML predictor
    prediction_type = db.Column(db.String(32), nullable=False, default="bayes")

    # Free-form disease label, e.g. "Cataract", "Diabetes", or the disease
    # the user was testing for in the Bayes calculator.
    disease = db.Column(db.String(120), nullable=True)

    # JSON-serialised inputs (prior, sensitivity, specificity, test_result,
    # or symptom list, etc.). Stored as text so we don't need a JSON column
    # type and stay portable across SQLite/MySQL/Postgres.
    inputs_json = db.Column(db.Text, nullable=True)

    # JSON-serialised outputs (posterior probability, risk band, top-k
    # predictions, confidence scores, …).
    results_json = db.Column(db.Text, nullable=True)

    # Convenience scalar columns so the history list can show useful info
    # without parsing the JSON blob for every row.
    probability = db.Column(db.Float, nullable=True)  # 0.0–1.0
    risk_level = db.Column(db.String(16), nullable=True)  # low/medium/high

    # Optional free-text note the user can attach to a history entry.
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )

    # Back-populate from User (set up the matching relationship on User
    # if you want bi-directional access; see __init__.py snippet).
    user = db.relationship(
        "User",
        backref=db.backref(
            "history_entries",
            lazy="dynamic",
            cascade="all, delete-orphan",
            order_by="PatientHistory.created_at.desc()",
        ),
    )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        """Serialise to a plain dict for JSON responses."""
        import json

        def _loads(blob):
            if not blob:
                return None
            try:
                return json.loads(blob)
            except (ValueError, TypeError):
                return None

        return {
            "id": self.id,
            "prediction_type": self.prediction_type,
            "disease": self.disease,
            "inputs": _loads(self.inputs_json),
            "results": _loads(self.results_json),
            "probability": self.probability,
            "probability_percent": (
                round(self.probability * 100, 2)
                if self.probability is not None
                else None
            ),
            "risk_level": self.risk_level,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() + "Z",
        }

    def __repr__(self) -> str:  # pragma: no cover - debug aid only
        return (
            f"<PatientHistory id={self.id} user_id={self.user_id} "
            f"type={self.prediction_type} disease={self.disease!r} "
            f"prob={self.probability}>"
        )
