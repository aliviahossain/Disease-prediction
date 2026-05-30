"""Test synthetic patient module."""

import pytest
from backend.models.ml_model import DiseaseMLModel
from backend.services.synthetic_patient_service import SyntheticPatientGenerator


def test_generate_single_patient():
    """Test single patient generation."""
    gen = SyntheticPatientGenerator()
    patient = gen.generate_patient(disease="diabetes", symptom_intensity=0.5)
    
    assert patient["disease"] == "diabetes"
    assert isinstance(patient["symptoms"], list)
    assert patient["age"] >= 0
    assert patient["is_synthetic"] is True
    assert "vitals" in patient


def test_generate_population():
    """Test population generation."""
    gen = SyntheticPatientGenerator()
    population = gen.generate_population(count=10)
    
    assert len(population) == 10
    assert all(p["is_synthetic"] for p in population)


def test_rare_combinations():
    """Test rare symptom combinations."""
    gen = SyntheticPatientGenerator()
    rare = gen.generate_rare_combinations(count=5)
    
    assert len(rare) == 5
    assert all("rarity_note" in p for p in rare)


def test_edge_cases():
    """Test edge case generation."""
    gen = SyntheticPatientGenerator()
    cases = gen.generate_edge_cases()
    
    assert len(cases) == 4  # High, low, pediatric, geriatric
    assert all(c["is_synthetic"] for c in cases)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
