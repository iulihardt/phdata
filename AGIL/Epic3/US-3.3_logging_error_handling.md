# US-3.3 — Structured Logging + Global Error Handling

**Epic**: E3 — Code Quality & Refactoring
**Priority**: Should | **Story Points**: 3

## User Story

As a developer operating this service in production, I want structured logs and consistent error responses, so that I can monitor the service and debug issues quickly.

## Acceptance Criteria

- [ ] Replace all `print()` statements with Python `logging` module
- [ ] Log level configurable via environment variable (default: INFO)
- [ ] Each request logs: endpoint, zipcode, whether imputation was used, response time
- [ ] Unhandled exceptions return a clean 500 JSON response (not HTML stack trace)
- [ ] Global exception handler catches unexpected errors and logs the traceback
- [ ] Startup logs confirm successful resource loading

## Technical Notes

- Use Python standard `logging` module with JSON-friendly format
- Add FastAPI exception handlers for `Exception` and `HTTPException`
- Add request timing middleware or decorator
- Environment variable: `LOG_LEVEL=INFO|DEBUG|WARNING|ERROR`

## Files to Modify/Create

- `src/main.py` — configure logging, add exception handlers
- `src/api/endpoints.py` — replace print with logger, add request logging
