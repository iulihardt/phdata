# US-3.3 — Structured Logging + Global Error Handling

**Epic**: E3 — Code Quality & Refactoring
**Priority**: Should | **Story Points**: 3
**Status**: DONE

## User Story

As a developer operating this service in production, I want structured logs and consistent error responses, so that I can monitor the service and debug issues quickly.

## Acceptance Criteria

- [x] Replace all `print()` statements with Python `logging` module
- [x] Log level configurable via environment variable (default: INFO)
- [x] Each request logs: endpoint, zipcode, whether imputation was used, response time
- [x] Unhandled exceptions return a clean 500 JSON response (not HTML stack trace)
- [x] Global exception handler catches unexpected errors and logs the traceback
- [x] Startup logs confirm successful resource loading

## Technical Notes

- Use Python standard `logging` module with JSON-friendly format
- Add FastAPI exception handlers for `Exception` and `HTTPException`
- Add request timing middleware or decorator
- Environment variable: `LOG_LEVEL=INFO|DEBUG|WARNING|ERROR`

## Files to Modify/Create

- `src/main.py` — configure logging, add exception handlers
- `src/api/endpoints.py` — replace print with logger, add request logging

---

## Implementation Summary

### What Was Done

1. **Configurable log level**: The `LOG_LEVEL` environment variable (default: `INFO`) controls the logging verbosity across the entire application. Supported values: `DEBUG`, `INFO`, `WARNING`, `ERROR`.

2. **Request logging middleware** (`src/main.py`): An HTTP middleware logs every request with `method`, `path`, `status_code`, and `duration_ms`. This provides visibility into API traffic and latency without any instrumentation in the endpoint layer.

3. **Per-prediction structured logging** (`src/api/endpoints.py`): Each prediction logs `zipcode`, `imputation_used` (boolean), and `predicted_price`. Failed predictions (e.g. unknown zipcode) are logged at WARNING level.

4. **Global error handling**: Unhandled exceptions are caught at the middleware level, logged with full traceback (at DEBUG level), and return a clean `{"detail": "Internal server error"}` JSON response with HTTP 500 — never exposing stack traces to clients.

5. **Tests**: Four new unit tests validate that (a) unhandled exceptions produce JSON 500 responses, (b) no internal details leak to clients, and (c) logs correctly reflect whether imputation was used per request.

### Attention Points

- The global exception handler is implemented inside the HTTP middleware (not as a standalone `@app.exception_handler(Exception)`) because Starlette's `BaseHTTPMiddleware` re-raises exceptions from `call_next()` before they reach registered exception handlers. Both layers are present for defense in depth.
- Log format uses key=value structured style for easy parsing by log aggregation tools (e.g. Datadog, Splunk, ELK).
- In production, consider adding a correlation/request ID to each log line for request tracing.

### Expected Business Improvement

This story makes the service **production-observable**. Operations teams can now:
- **Monitor API health** through structured request logs (latency, error rates, imputation frequency)
- **Debug issues faster** because errors include full context without exposing internals to end users
- **Adjust verbosity dynamically** by changing the `LOG_LEVEL` environment variable without code changes
- **Integrate with monitoring tools** (Datadog, CloudWatch, Grafana) since logs follow a structured key=value format

The net result is reduced mean-time-to-resolution (MTTR) for production incidents and better visibility into how the prediction service is being used.
