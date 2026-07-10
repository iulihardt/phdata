# US-5.1 — Update README + API Documentation

**Epic**: E5 — Documentation & Presentation
**Priority**: Must | **Story Points**: 3

## User Story

As a developer or reviewer, I want up-to-date documentation that explains how to run the system and what changed, so that I can understand and use the API without reading all the source code.

## Acceptance Criteria

- [ ] README reflects the new imputation capability with examples
- [ ] README documents performance improvements made
- [ ] README lists any new dependencies added
- [ ] API endpoint documentation includes examples with null fields
- [ ] Swagger/OpenAPI auto-docs show field descriptions, constraints, and examples
- [ ] Setup instructions still work end-to-end (Docker build + run + test)

## Technical Notes

- Update `README.md` with new sections for imputation and performance
- Add `example` and `description` to Pydantic model fields for richer Swagger docs
- Verify the Docker build/run instructions still work after all changes

## Files to Modify

- `README.md` — update with new features and instructions
- `src/api/endpoints.py` — enrich Pydantic model with OpenAPI metadata
