# US-3.2 — Input Validation with Clear Error Messages

**Epic**: E3 — Code Quality & Refactoring
**Priority**: Must | **Story Points**: 2

## User Story

As an API consumer, I want descriptive validation errors when I send bad data, so that I know exactly which field is wrong and how to fix it.

## Acceptance Criteria

- [ ] Pydantic validators enforce value ranges (e.g., bedrooms >= 0, sqft_living > 0)
- [ ] Error responses include the field name and what was wrong
- [ ] Consistent error response format across all validation failures
- [ ] API docs (Swagger UI) show field constraints and examples

## Technical Notes

- Use Pydantic `@field_validator` or `Field(ge=0)` constraints
- Add `example` values in the Pydantic model for Swagger docs
- Coordinate with US-1.3 (edge cases) — validation rules should be defined here, edge case handling uses them

## Files to Modify

- `src/api/endpoints.py` — add validators and Field constraints to `HomeFeatures`

---

## Implementation Summary

### What Was Done

1. **Replaced manual `@field_validator` with declarative `Field()` constraints** (`src/api/endpoints.py`) — Each field in `HomeFeatures` now has its own constraint, description, and example value defined via Pydantic's `Field()`. This is idiomatic Pydantic v2 and auto-generates accurate OpenAPI/Swagger documentation.
   - `bedrooms`: `ge=0` (studios have 0 bedrooms)
   - `bathrooms`: `ge=0`
   - `sqft_living`: `gt=0` (a home must have positive living area)
   - `sqft_lot`: `gt=0` (lot size must be positive)
   - `floors`: `gt=0` (at least one floor or half-floor)
   - `sqft_above`: `ge=0`
   - `sqft_basement`: `ge=0` (0 means no basement)
   - `zipcode`: `pattern=r"^\d{5}$"` (must be exactly 5 digits)

2. **Added a custom `RequestValidationError` handler** (`src/main.py`) — All validation errors now return a clean, consistent JSON format: `{"detail": [{"field": "...", "message": "..."}]}`. This replaces the verbose default Pydantic/FastAPI error response which included internal fields like `type`, `ctx`, and `url` that are meaningless to API consumers.

3. **Enhanced API metadata** (`src/main.py`) — Added `title`, `description`, and `version` to the FastAPI app for better Swagger UI presentation.

4. **Added 9 new unit tests** (`test/unit/test_api_unit.py`) — Covering zipcode format validation (letters, too short, too long), zero-value boundary checks (`sqft_living=0` rejected, `bedrooms=0` accepted, `sqft_basement=0` accepted), error format consistency, and multiple simultaneous validation errors. All 19 tests pass with 97% code coverage.

### Acceptance Criteria Status

- [x] Pydantic validators enforce value ranges (e.g., bedrooms >= 0, sqft_living > 0)
- [x] Error responses include the field name and what was wrong
- [x] Consistent error response format across all validation failures
- [x] API docs (Swagger UI) show field constraints and examples

### Points of Attention

1. **Zipcode validation is two-layered** — The regex pattern `^\d{5}$` catches malformed zipcodes at the schema level (422 response), while the `PredictionService` raises `ValueError` for valid-format zipcodes not found in demographics data (400 response). This gives consumers clear, distinct error messages for "bad format" vs. "not in our coverage area".

2. **`gt=0` vs `ge=0` trade-off** — `sqft_living`, `sqft_lot`, and `floors` use `gt=0` (strictly positive) because a property cannot have zero living area, zero lot, or zero floors. Other fields like `bedrooms` and `sqft_basement` use `ge=0` since zero is a valid real-world value (studios and homes without basements).

3. **No upper-bound constraints** — Upper bounds were intentionally omitted to avoid rejecting legitimate outliers (e.g., mansions with 10+ bedrooms or very large lots). The model will produce predictions for extreme values; it is better to let the ML model handle these than to hard-reject valid data at the API boundary.

4. **Backward-compatible error format** — Existing API consumers that check for `"detail"` in the response body will continue to work. The change only simplifies the structure of each error entry.

### Expected Improvements (Business Perspective)

This story improves the experience for any system or person sending data to the API:

- **Faster debugging for integrators**: When a partner system sends bad data, the error response now clearly states which field failed and why (e.g., `"field": "sqft_living", "message": "Input should be greater than 0"`). This eliminates guesswork and reduces support tickets.
- **Data quality protection**: Invalid inputs (negative values, impossible zeros, malformed zipcodes) are rejected before they reach the prediction model. This prevents nonsensical price estimates from being served to end users.
- **Self-documenting API**: The Swagger UI at `/docs` now shows every field's constraints, description, and example value. New integrators can understand the API contract without reading external documentation.
- **Reduced integration time**: Partners building against the API can validate their payloads locally using the Swagger page, reducing back-and-forth communication during onboarding.
