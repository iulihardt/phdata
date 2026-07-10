# US-4.2 — Performance / Load Tests

**Epic**: E4 — Testing & Validation
**Priority**: Should | **Story Points**: 3

## User Story

As a developer, I want automated performance tests that verify the API meets latency targets, so that performance regressions are caught before deployment.

## Acceptance Criteria

- [ ] Test sends at least 50 sequential requests and measures response times
- [ ] Asserts average response time < 100ms (post-optimization)
- [ ] Asserts p95 response time < 200ms
- [ ] Tests both complete requests and requests with missing data
- [ ] Test can run inside Docker environment
- [ ] Results are printed in a readable format

## Technical Notes

- Can be a pytest test or standalone script
- Use `time.perf_counter()` for precise timing
- Run against the FastAPI TestClient (in-process) for unit-level perf tests
- Optionally run against Docker container for integration-level perf tests
- Complements US-2.2 (benchmark) — this is the automated/CI version

## Files to Create

- `test/performance/test_latency.py` — performance test suite
