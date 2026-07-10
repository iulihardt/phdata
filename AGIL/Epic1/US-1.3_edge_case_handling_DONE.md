# US-1.3 — Edge Case Handling

**Epic**: E1 — Missing Data Handling (KNN Imputation)
**Priority**: Must | **Story Points**: 3

## User Story

As an API consumer, I want clear and helpful error messages when I submit invalid data, so that I can correct my request without guessing what went wrong.

## Acceptance Criteria

- [x] Invalid zipcode (not found in demographics data) returns 400 with message: zipcode not found
- [x] All numeric fields null (only zipcode provided) still produces a prediction via imputation
- [x] Invalid types (e.g., string where number expected) return 422 with field-level errors
- [x] Negative values for fields like sqft_living are rejected with a descriptive error
- [x] Empty request body returns 422
- [x] Response error format is consistent: `{"detail": "..."}`

## Technical Notes

- Add Pydantic validators (`@field_validator`) for value range checks
- Validate zipcode against the loaded demographics data in the endpoint
- Test with the edge cases from `future_unseen_examples.csv`

## Files to Modify

- `src/api/endpoints.py` — validators and zipcode check

---

## Implementation Notes

### What Was Done

**`src/api/endpoints.py`**

1. **Non-negative field validator** — Added a single `@field_validator` decorated with `@classmethod` covering all seven optional numeric fields (`bedrooms`, `bathrooms`, `sqft_living`, `sqft_lot`, `floors`, `sqft_above`, `sqft_basement`). When any of these fields is provided (not `None`) and its value is negative, Pydantic raises a `ValueError("must be a non-negative number")`, which FastAPI automatically converts to a `422 Unprocessable Entity` response with field-level detail — consistent with the required `{"detail": "..."}` format.

2. **Zipcode validation** — After filtering the demographics CSV for the requested zipcode, the endpoint now checks whether the resulting DataFrame is empty. If so, it raises `HTTPException(status_code=400, detail="zipcode not found")`, satisfying the 400 contract with a machine-readable message.

**`test/unit/test_api_unit.py`**

Five new edge-case tests were added:

| Test | Scenario | Expected |
|------|----------|----------|
| `test_invalid_zipcode_returns_400` | Zipcode `"00000"` not in demographics | 400 + `{"detail": "zipcode not found"}` |
| `test_negative_sqft_living_returns_422` | `sqft_living: -100.0` | 422 with detail |
| `test_negative_bedrooms_returns_422` | `bedrooms: -3` | 422 with detail |
| `test_invalid_type_returns_422` | `sqft_living: "big house"` | 422 with detail |
| `test_empty_body_returns_422` | `{}` (no zipcode) | 422 (zipcode is required) |

All 10 unit tests pass (5 pre-existing + 5 new) — verified inside the Docker test image.

### Points of Attention

- **422 for type errors is native Pydantic/FastAPI behaviour** — no extra code was needed; it works out of the box as long as the model fields are properly typed.
- **Empty body → 422 is also native** — because `zipcode: str` (no `Optional`, no default) is a required field; omitting it triggers Pydantic validation failure automatically.
- **All-nulls prediction still works** — the KNN imputer (fitted at startup) fills every missing numeric feature, so a request with only `zipcode` produces a valid prediction. This was already covered by `test_predict_only_zipcode_required` and was not broken by this change.
- **`home_features.dict()` deprecation warning** — Pydantic v2 recommends `model_dump()` over `.dict()`. This is a pre-existing issue; suppressing it is deferred to US-3.1 (refactoring), where `endpoints.py` will be cleaned up holistically.
- **Demographics CSV is still loaded on every request** — this is a known performance issue addressed by US-2.1 (startup preloading); it is intentionally left out of scope here.
