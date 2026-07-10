# US-3.1 — Refactor Endpoints & Project Structure

**Epic**: E3 — Code Quality & Refactoring
**Priority**: Must | **Story Points**: 3

## User Story

As a developer maintaining this codebase, I want clean separation of concerns and organized code structure, so that the project is easy to navigate and extend.

## Acceptance Criteria

- [ ] `endpoints.py` only handles HTTP concerns (request parsing, response formatting)
- [ ] Business logic (imputation, prediction) lives in dedicated service modules
- [ ] `loader.py` utilities are actually used (currently ignored)
- [ ] No inline file I/O in endpoint handlers
- [ ] Dependencies in `requirements.txt` have pinned versions
- [ ] Imports are clean and organized

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
