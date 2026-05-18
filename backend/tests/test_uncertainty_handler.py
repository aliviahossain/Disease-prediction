"""
tests/test_uncertainty_handler.py
----------------------------------
pytest tests/test_uncertainty_handler.py -v
 
Covers every acceptance criterion from GitHub issue #226:
  ✓  Confidence threshold is configurable and documented.
  ✓  Model detects and handles low-confidence predictions.
  ✓  User sees a clear message when prediction confidence is insufficient.
  ✓  Existing high-confidence predictions continue to work as expected.
"""
 
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
 
import pytest
from backend.utils.uncertainty_handler import UncertaintyHandler, CONFIDENCE_THRESHOLD
 
 
# ── Acceptance criterion 1 — Configurable threshold ─────────────────────────
 
class TestConfiguration:
    def test_default_threshold_equals_env_default(self):
        h = UncertaintyHandler()
        assert h.confidence_threshold == CONFIDENCE_THRESHOLD
 
    def test_custom_thresholds_stored(self):
        h = UncertaintyHandler(confidence_threshold=0.65, margin_threshold=0.05)
        assert h.confidence_threshold == 0.65
        assert h.margin_threshold == 0.05
 
    def test_get_config_returns_both_thresholds(self):
        h = UncertaintyHandler(confidence_threshold=0.55, margin_threshold=0.08)
        cfg = h.get_config()
        assert cfg['confidence_threshold'] == 0.55
        assert cfg['margin_threshold'] == 0.08
 
    def test_invalid_confidence_raises(self):
        with pytest.raises(ValueError):
            UncertaintyHandler(confidence_threshold=1.5)
 
    def test_invalid_margin_raises(self):
        with pytest.raises(ValueError):
            UncertaintyHandler(margin_threshold=-0.01)
 
 
# ── Acceptance criterion 2 — Low-confidence detection ───────────────────────
 
class TestLowConfidenceDetection:
    def setup_method(self):
        self.h = UncertaintyHandler(confidence_threshold=0.40, margin_threshold=0.10)
 
    def test_below_threshold_is_insufficient(self):
        result = self.h.evaluate(confidence_score=0.25)
        assert result['is_sufficient'] is False
 
    def test_exactly_at_threshold_is_sufficient(self):
        # Score exactly at the threshold should pass (>= not >)
        result = self.h.evaluate(confidence_score=0.40, top2_score=0.10)
        assert result['is_sufficient'] is True
 
    def test_narrow_margin_is_insufficient(self):
        # Both above threshold but too close together
        result = self.h.evaluate(
            confidence_score=0.45, top2_score=0.43,
            disease_name='Flu', top2_disease='Cold'
        )
        assert result['is_sufficient'] is False
 
    def test_sufficient_margin_is_ok(self):
        result = self.h.evaluate(confidence_score=0.72, top2_score=0.15)
        assert result['is_sufficient'] is True
 
    def test_no_top2_skips_margin_check(self):
        # If there is no second prediction, margin check must not fire
        result = self.h.evaluate(confidence_score=0.55, top2_score=None)
        assert result['is_sufficient'] is True
 
    def test_confidence_preserved_in_result(self):
        result = self.h.evaluate(confidence_score=0.28)
        assert abs(result['confidence'] - 0.28) < 1e-9
 
 
# ── Acceptance criterion 3 — Clear user-facing message ──────────────────────
 
class TestUserFacingMessages:
    def setup_method(self):
        self.h = UncertaintyHandler(confidence_threshold=0.40, margin_threshold=0.10)
 
    def test_reason_is_non_empty_for_low_confidence(self):
        result = self.h.evaluate(confidence_score=0.20)
        assert result['reason'] is not None
        assert len(result['reason']) > 20
 
    def test_reason_mentions_threshold_percentage(self):
        result = self.h.evaluate(confidence_score=0.20)
        assert '%' in result['reason']
 
    def test_reason_mentions_disease_names_for_margin_fail(self):
        result = self.h.evaluate(
            confidence_score=0.44, top2_score=0.42,
            disease_name='Dengue', top2_disease='Malaria'
        )
        assert 'Dengue' in result['reason']
        assert 'Malaria' in result['reason']
 
    def test_reason_is_none_when_sufficient(self):
        result = self.h.evaluate(confidence_score=0.80, top2_score=0.05)
        assert result['reason'] is None
 
 
# ── Acceptance criterion 4 — High-confidence predictions unchanged ───────────
 
class TestHighConfidencePredictions:
    def setup_method(self):
        self.h = UncertaintyHandler(confidence_threshold=0.40, margin_threshold=0.10)
 
    def test_high_score_is_sufficient(self):
        result = self.h.evaluate(confidence_score=0.88, top2_score=0.07)
        assert result['is_sufficient'] is True
 
    def test_medium_score_with_clear_margin_is_sufficient(self):
        result = self.h.evaluate(confidence_score=0.55, top2_score=0.20)
        assert result['is_sufficient'] is True
 
    def test_low_threshold_variant_accepts_lower_score(self):
        h = UncertaintyHandler(confidence_threshold=0.25, margin_threshold=0.05)
        result = h.evaluate(confidence_score=0.30, top2_score=0.10)
        assert result['is_sufficient'] is True
 
    def test_strict_threshold_rejects_borderline(self):
        h = UncertaintyHandler(confidence_threshold=0.70, margin_threshold=0.15)
        result = h.evaluate(confidence_score=0.65, top2_score=0.10)
        assert result['is_sufficient'] is False
 
    def test_strict_threshold_accepts_high_confidence(self):
        h = UncertaintyHandler(confidence_threshold=0.70, margin_threshold=0.15)
        result = h.evaluate(confidence_score=0.90, top2_score=0.05)
        assert result['is_sufficient'] is True