# Backlog Overview

## Execution Order

E2 (Performance) -> E1 (Imputation) -> E3 (Code Quality) -> E4 (Testing) -> E5 (Documentation)

**Rationale**: Fix performance first (quick win, removes I/O on every request), then implement the core feature (imputation), then clean up code quality, validate with tests, and finally document everything.

## Epics

| Epic | Title | Stories | Story Points | Priority |
|------|-------|---------|-------------|----------|
| E1 | Missing Data Handling (KNN Imputation) | 3 | 10 | Must |
| E2 | API Performance Optimization | 2 | 5 | Must |
| E3 | Code Quality & Refactoring | 3 | 8 | Must/Should |
| E4 | Testing & Validation | 2 | 8 | Must/Should |
| E5 | Documentation & Presentation | 2 | 6 | Must |

**Total: 12 Stories / 37 Story Points**

## Stories Summary

| ID | Story | MoSCoW | SP |
|----|-------|--------|-----|
| US-1.1 | Nullable schema fields (all except zipcode) | Must | 2 |
| US-1.2 | KNN Imputation service + pipeline integration | Must | 5 |
| US-1.3 | Edge case handling (invalid zipcode, all nulls, bad types) | Must | 3 |
| US-2.1 | Preload model, features, demographics & imputer at startup | Must | 3 |
| US-2.2 | Latency benchmark (before/after comparison) | Should | 2 |
| US-3.1 | Refactor endpoints.py, use loader.py, organize structure | Must | 3 |
| US-3.2 | Input validation with clear error messages (Pydantic) | Must | 2 |
| US-3.3 | Structured logging + global error handling | Should | 3 |
| US-4.1 | Unit + endpoint tests for imputation (happy path, edge cases, unseen data) | Must | 5 |
| US-4.2 | Performance/load test with latency metrics (p50/p95/p99) | Should | 3 |
| US-5.1 | Update README + API docs (OpenAPI examples) | Must | 3 |
| US-5.2 | Business presentation (slides) + technical live demo | Must | 3 |

## Definition of Done

- Code passes all unit and integration tests
- Docker build succeeds and API responds correctly
- Changes are documented in README
- No regressions in existing prediction accuracy
