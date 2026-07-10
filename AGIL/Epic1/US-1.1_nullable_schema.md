# US-1.1 — Nullable Schema Fields

**Epic**: E1 — Missing Data Handling (KNN Imputation)
**Priority**: Must | **Story Points**: 2

## User Story

As an API consumer, I want to submit property data with missing fields (null values) for any field except zipcode, so that I can get predictions even when I don't have complete property information.

## Acceptance Criteria

- [ ] All fields in the `HomeFeatures` Pydantic model accept `None` except `zipcode`
- [ ] `zipcode` remains required (non-nullable `str`)
- [ ] Requests with `null` fields return 200 (not 422 validation error)
- [ ] Requests with missing `zipcode` return 422 with a clear error message
- [ ] Field types remain enforced when values are provided (e.g., `bedrooms` must be int or null, not a string)

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
