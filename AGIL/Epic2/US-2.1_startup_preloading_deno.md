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

---

## Implementation Notes

### What Was Done

All acceptance criteria were met. The following changes were applied:

**`src/utils/loader.py`**
- Removed the old `get_demographics(zipcode, path)` helper that read the CSV and filtered by zipcode on every call.
- Added `load_demographics(path) -> pd.DataFrame` which reads the full CSV once and returns the entire DataFrame in memory.
- Cleaned up unused `import os`; standardised quote style.

**`src/main.py`**
- Extended the existing `lifespan` context manager (which already fitted the KNN imputer) to also preload the ML model via `load_model()`, the feature list via `load_features()`, and the demographics DataFrame via `load_demographics()`.
- Each resource is stored in `app.state` (`app.state.model`, `app.state.model_features`, `app.state.demographics`, `app.state.imputer`).
- Added `logging` with `INFO`-level messages for each step so operators can confirm resources loaded successfully in container logs.

**`src/api/endpoints.py`**
- Removed the three blocking I/O operations that previously ran on every POST (`pickle.load`, `json.load`, `pd.read_csv`).
- Removed the now-unused `import json` and `import pickle`.
- The endpoint now reads all four resources from `request.app.state`; the only computation per request is the imputation transform, the DataFrame merge, and the model inference.
- Replaced deprecated `home_features.dict()` with `home_features.model_dump()` (Pydantic v2).

### Acceptance Criteria Status

- [x] Model (`model.pkl`) is loaded once at application startup, not on every request
- [x] Feature metadata (`model_features.json`) is loaded once at startup
- [x] Demographics data (`zipcode_demographics.csv`) is loaded once at startup
- [x] KNN Imputer is fitted once at startup
- [x] All preloaded resources are accessible to the endpoint handler without re-reading from disk
- [x] Application startup logs confirm all resources were loaded successfully
- [x] First request is as fast as subsequent requests (no cold-start penalty per request)

### Points of Attention

- **Startup time increases slightly**: Fitting the KNN imputer on the full training dataset (~21k rows) takes a few seconds at startup. This is an intentional trade-off — it completely eliminates per-request I/O and fitting cost.
- **Memory footprint**: The model, feature list, demographics DataFrame (~71 zipcodes), and fitted imputer are all kept in RAM. For the current dataset size this is negligible, but should be considered if the demographics file grows significantly.
- **`app.state` is not thread-safe for mutation**: Resources are written once during startup (before any requests are served) and are read-only afterwards, so no locking is required.
- **Docker path aliases**: The Dockerfile already creates symlinks `/app/model → /app/src/model` and `/app/data → /app/src/data`, so the path strings used in `lifespan` (`"model/model.pkl"`, `"data/..."`) work identically inside and outside the container.
- **Test coverage**: All 10 unit tests pass with 97% overall coverage after the refactor. The `endpoints.py` module reached 100% coverage.
