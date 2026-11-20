# Synthetic Patient Simulation Module

## Overview

Generates realistic synthetic patient profiles for:
- Testing model with rare disease combinations
- Edge-case probability scenarios
- Stress testing the prediction system
- Research and educational use

## Files Added

1. **`backend/services/synthetic_patient_service.py`** - Core generator
2. **`backend/routes/synthetic_routes.py`** - REST API endpoints
3. **`backend/models/prediction.py`** - Added `is_synthetic` flag to track synthetic vs real predictions

## API Endpoints

All endpoints are under `/api/synthetic/`

### Generate Single Patient
```
POST /api/synthetic/generate
Body: {
    "disease": "diabetes" (optional),
    "symptom_intensity": 0.5 (0.0-1.0),
    "age": 45 (optional)
}
Response: {"status": "success", "patient": {...}}
```

### Generate Population
```
POST /api/synthetic/population
Body: {"count": 50}
Response: {"status": "success", "count": 50, "population": [...]}
```

### Generate Rare Combinations
```
GET /api/synthetic/rare?count=10
Response: {"status": "success", "count": 10, "combinations": [...]}
```

### Generate Edge Cases
```
GET /api/synthetic/edge-cases
Response: {"status": "success", "count": 4, "cases": [...]}
```

## Database Changes

- **Column Added**: `PredictionHistory.is_synthetic` (Boolean, default=False)
- Automatically set to `True` for synthetic predictions
- Filters available in history queries to separate real vs synthetic

## Usage Example

```python
from backend.services.synthetic_patient_service import SyntheticPatientGenerator

gen = SyntheticPatientGenerator()

# Single patient
patient = gen.generate_patient(disease="diabetes", symptom_intensity=0.7)

# Population
population = gen.generate_population(count=100)

# Rare combinations
rare = gen.generate_rare_combinations(count=5)

# Edge cases
edge_cases = gen.generate_edge_cases()
```

## Design Decisions

- **Minimal Scope**: Only core generation features
- **No Breaking Changes**: Existing functionality unaffected
- **Opt-in**: Synthetic data marked clearly, doesn't affect regular predictions
- **Simple Integration**: Uses existing disease weights from ML model
