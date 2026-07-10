# US-2.1 — Preload Resources at Startup

**Epic**: E2 — API Performance Optimization
**Priority**: Must | **Story Points**: 3

## User Story

As an API consumer, I want fast response times on every request, so that the service is usable in production with real-time user interactions.

## Acceptance Criteria

- [ ] Model (`model.pkl`) is loaded once at application startup, not on every request
- [ ] Feature metadata (`model_features.json`) is loaded once at startup
- [ ] Demographics data (`zipcode_demographics.csv`) is loaded once at startup
- [ ] KNN Imputer is fitted once at startup
- [ ] All preloaded resources are accessible to the endpoint handler without re-reading from disk
- [ ] Application startup logs confirm all resources were loaded successfully
- [ ] First request is as fast as subsequent requests (no cold-start penalty per request)

## Technical Notes

- Use FastAPI `lifespan` event or `@app.on_event("startup")` to load resources
- Store loaded resources in app state or a singleton/module-level variable
- Current bottleneck in `src/api/endpoints.py` lines 33-43: opens files on every POST
- `src/utils/loader.py` already has helper functions — use them

## Files to Modify

- `src/main.py` — add startup event
- `src/api/endpoints.py` — remove per-request loading, use preloaded resources
- `src/utils/loader.py` — extend with demographics and imputer loading
