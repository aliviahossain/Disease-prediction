"""
Model versioning and management for continuous improvement.

Enables tracking model versions, retraining with latest research, 
and rollback on performance degradation.
"""

import json
from datetime import datetime
from typing import Dict, List


class ModelVersion:
    """Manages model versions and metadata."""

    def __init__(self, version: str, trained_date: str, accuracy: float, source: str):
        self.version = version
        self.trained_date = trained_date
        self.accuracy = accuracy
        self.source = source  # "initial", "research_update", "feedback_trained"
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "trained_date": self.trained_date,
            "accuracy": self.accuracy,
            "source": self.source,
            "created_at": self.created_at,
        }


class ModelVersionManager:
    """Manages model versions and training cycles."""

    def __init__(self):
        self.versions: List[ModelVersion] = []
        self.current_version = None
        self.training_log = []

    def register_version(
        self, version: str, trained_date: str, accuracy: float, source: str
    ) -> ModelVersion:
        """Register a new model version."""
        mv = ModelVersion(version, trained_date, accuracy, source)
        self.versions.append(mv)
        self.current_version = mv
        return mv

    def get_current_version(self) -> Dict:
        """Get current active model version."""
        if self.current_version:
            return self.current_version.to_dict()
        return None

    def get_version_history(self) -> List[Dict]:
        """Get all version history."""
        return [
            v.to_dict()
            for v in sorted(self.versions, key=lambda x: x.created_at, reverse=True)
        ]

    def can_rollback(self, target_version: str) -> bool:
        """Check if rollback is possible."""
        versions = [v.version for v in self.versions]
        return target_version in versions

    def log_training(self, trigger: str, status: str, notes: str):
        """Log training event."""
        self.training_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "trigger": trigger,  # "scheduled", "research_update", "feedback"
                "status": status,  # "started", "completed", "failed"
                "notes": notes,
            }
        )

    def export_metadata(self) -> Dict:
        """Export version metadata for audit trail."""
        return {
            "current_version": self.get_current_version(),
            "version_history": self.get_version_history(),
            "training_log": self.training_log,
        }


# Singleton instance
_version_manager = None


def get_version_manager() -> ModelVersionManager:
    """Get or create version manager singleton."""
    global _version_manager
    if _version_manager is None:
        _version_manager = ModelVersionManager()
    return _version_manager
