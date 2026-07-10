# US-3.1 — Refactor Endpoints & Project Structure ✅ DONE

**Epic**: E3 — Code Quality & Refactoring
**Priority**: Must | **Story Points**: 3

## User Story

As a developer maintaining this codebase, I want clean separation of concerns and organized code structure, so that the project is easy to navigate and extend.

## Acceptance Criteria

- [x] `endpoints.py` only handles HTTP concerns (request parsing, response formatting)
- [x] Business logic (imputation, prediction) lives in dedicated service modules
- [x] `loader.py` utilities are actually used (currently ignored)
- [x] No inline file I/O in endpoint handlers
- [x] Dependencies in `requirements.txt` have pinned versions
- [x] Imports are clean and organized

## Technical Notes

- Current `endpoints.py` does everything: file loading, data merging, prediction
- Suggested structure:
  ```
  src/
    api/endpoints.py        # HTTP layer only
    services/imputer.py     # Imputation logic
    services/predictor.py   # Prediction orchestration
    utils/loader.py         # Resource loading
  ```
- Move prediction orchestration out of the endpoint

## Files to Modify/Create

- `src/api/endpoints.py` — slim down to HTTP concerns
- `src/services/predictor.py` — new: prediction orchestration
- `src/utils/loader.py` — extend and actually use
- `requirements.txt` — pin versions

---

## Implementation Summary

### What Was Done

1. **Created `src/services/predictor.py`** — A new `PredictionService` class that encapsulates the full prediction pipeline: KNN imputation → demographic data lookup → feature selection → model prediction. The service receives all its dependencies (model, feature list, demographics DataFrame, imputer) via constructor injection, making it fully testable and decoupled from the HTTP layer.

2. **Simplified `src/api/endpoints.py`** — Removed all business logic (DataFrame manipulation, demographic lookups, model calls). The endpoint now only handles HTTP concerns: parsing the incoming request via the Pydantic `HomeFeatures` model, delegating to `PredictionService`, and formatting the JSON response. The `pandas` import was also removed since it is no longer needed here.

3. **Updated `src/main.py`** — The lifespan startup now assembles all loaded resources into a single `PredictionService` instance stored in `app.state.prediction_service`, instead of exposing raw model, features, demographics, and imputer as separate state attributes. This provides a cleaner public API surface for the application state.

4. **Pinned dependency versions in `requirements.txt`** — All six direct dependencies now have exact version pins (e.g., `fastapi==0.139.0`, `scikit-learn==1.7.2`), ensuring deterministic Docker builds and eliminating the risk of silent breakage from upstream releases.

### Attention Points

- **No breaking changes to the API contract** — The `/predict` and `/health` endpoints behave identically to before. All 10 existing unit tests pass with 97% code coverage.
- **PredictionService raises `ValueError`** for unknown zipcodes instead of `HTTPException`, keeping the service layer framework-agnostic. The endpoint translates this into the same HTTP 400 response clients already expect.
- **No changes to `loader.py`** — It was already being used correctly in `main.py` from a previous story (US-2.1). No extension was needed.

### Expected Improvements (Business Perspective)

This refactoring does not change what the API does — it changes how it is organized internally. The benefits are:

- **Faster feature development**: New capabilities (e.g., batch predictions, confidence intervals, model versioning) can be added to the `PredictionService` without touching the HTTP layer, reducing the risk of introducing bugs.
- **Easier onboarding**: New developers can understand the codebase faster because each file has a single, clear responsibility.
- **More reliable deployments**: Pinned dependency versions mean the application builds the same way every time, eliminating "it worked on my machine" surprises.
- **Better testability**: The prediction logic can now be tested in isolation (without spinning up an HTTP server), enabling faster and more targeted quality checks.
