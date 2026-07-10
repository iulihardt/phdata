# US-4.1 — Unit + Endpoint Tests for Imputation

**Epic**: E4 — Testing & Validation
**Priority**: Must | **Story Points**: 5

## User Story

As a developer, I want comprehensive tests for the imputation feature, so that I can confidently deploy knowing missing data is handled correctly.

## Acceptance Criteria

- [ ] Unit tests for the imputation service in isolation
- [ ] Endpoint tests: request with all fields present returns correct prediction
- [ ] Endpoint tests: request with 1 missing field returns valid prediction
- [ ] Endpoint tests: request with multiple missing fields returns valid prediction
- [ ] Endpoint tests: request with all fields null except zipcode returns valid prediction
- [ ] Endpoint tests: request with missing zipcode returns 422
- [ ] Endpoint tests: request with invalid zipcode returns 400
- [ ] Validation against `future_unseen_examples.csv` — predictions are within reasonable range
- [ ] All existing tests still pass (no regressions)

## Technical Notes

- Use FastAPI `TestClient` for endpoint tests
- Use pytest fixtures for test data
- Compare imputed predictions against full-data predictions to verify reasonableness
- Load `future_unseen_examples.csv` as parametrized test cases

## Files to Modify/Create

- `test/unit/test_imputer.py` — new: imputation unit tests
- `test/unit/test_api_unit.py` — extend with missing data test cases
- `test/integration/test_api_integration.py` — extend with missing data scenarios
