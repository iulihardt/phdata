# US-1.3 — Edge Case Handling

**Epic**: E1 — Missing Data Handling (KNN Imputation)
**Priority**: Must | **Story Points**: 3

## User Story

As an API consumer, I want clear and helpful error messages when I submit invalid data, so that I can correct my request without guessing what went wrong.

## Acceptance Criteria

- [ ] Invalid zipcode (not found in demographics data) returns 400 with message: zipcode not found
- [ ] All numeric fields null (only zipcode provided) still produces a prediction via imputation
- [ ] Invalid types (e.g., string where number expected) return 422 with field-level errors
- [ ] Negative values for fields like sqft_living are rejected with a descriptive error
- [ ] Empty request body returns 422
- [ ] Response error format is consistent: `{"detail": "..."}`

## Technical Notes

- Add Pydantic validators (`@field_validator`) for value range checks
- Validate zipcode against the loaded demographics data in the endpoint
- Test with the edge cases from `future_unseen_examples.csv`

## Files to Modify

- `src/api/endpoints.py` — validators and zipcode check
