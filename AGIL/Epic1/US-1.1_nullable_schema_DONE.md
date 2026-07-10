# US-1.1 — Nullable Schema Fields

**Epic**: E1 — Missing Data Handling (KNN Imputation)
**Priority**: Must | **Story Points**: 2

## User Story

As an API consumer, I want to submit property data with missing fields (null values) for any field except zipcode, so that I can get predictions even when I don't have complete property information.

## Acceptance Criteria

- [x] All fields in the `HomeFeatures` Pydantic model accept `None` except `zipcode`
- [x] `zipcode` remains required (non-nullable `str`)
- [ ] Requests with `null` fields return 200 (not 422 validation error)
- [x] Requests with missing `zipcode` return 422 with a clear error message
- [x] Field types remain enforced when values are provided (e.g., `bedrooms` must be int or null, not a string)

## Technical Notes

- Modify `HomeFeatures` in `src/api/endpoints.py`
- Use `Optional[int]`, `Optional[float]` with `default=None`
- Example valid request:
  ```json
  {
    "bedrooms": 3,
    "bathrooms": null,
    "sqft_living": 2000,
    "sqft_lot": null,
    "floors": 2,
    "sqft_above": 1500,
    "sqft_basement": 500,
    "zipcode": "98125"
  }
  ```

## Files to Modify

- `src/api/endpoints.py` — `HomeFeatures` model

---

## Implementation Notes

### What was done

- Added `from typing import Optional` to `src/api/endpoints.py`.
- Changed all numeric fields in the `HomeFeatures` Pydantic model to `Optional[<type>] = None`:
  `bedrooms`, `bathrooms`, `sqft_living`, `sqft_lot`, `floors`, `sqft_above`, `sqft_basement`.
- `zipcode` remains a required, non-nullable `str`.
- No other files were modified; the change is limited to the schema definition.

### Acceptance criteria status

| Criterion | Status | Notes |
|-----------|--------|-------|
| All fields accept `None` except `zipcode` | Done | `Optional` types with `default=None` |
| `zipcode` remains required | Done | Kept as plain `str` |
| Null fields return 200 | **Partial** | Schema validation passes (no 422), but the predict endpoint will still fail with 500 until imputation is implemented in US-1.2 |
| Missing `zipcode` returns 422 | Done | Pydantic enforces required fields automatically |
| Type enforcement preserved | Done | `Optional[int]` still rejects non-int/non-null values |

### Attention points

1. **Requests with null fields will return 500 (not 200) until US-1.2 is completed.**
   The schema now allows nulls through validation, but the downstream prediction pipeline (`model.predict`) cannot handle `NaN` values. The full 200-response behavior depends on the KNN imputation service from US-1.2.
2. **The `home_features.dict()` call on line 40 will serialize `None` fields as `None`**, which pandas converts to `NaN`. This is the expected input format for `KNNImputer` in US-1.2.
3. **No regression on existing behavior**: requests with all fields fully populated continue to work exactly as before.


In that point the API acpte Null values but the model do not accpet so we need go to the history 1.2