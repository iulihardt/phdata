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
