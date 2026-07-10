# US-2.2 — Latency Benchmark (Before/After)

**Epic**: E2 — API Performance Optimization
**Priority**: Should | **Story Points**: 2

## User Story

As a developer, I want measurable evidence that the performance optimizations reduced response times, so that I can present concrete improvements to stakeholders.

## Acceptance Criteria

- [ ] Benchmark script that sends N requests (e.g., 100) to the `/predict` endpoint
- [ ] Captures latency metrics: min, max, mean, p50, p95, p99
- [ ] Results documented with before/after comparison
- [ ] At least 5x improvement in average response time after optimizations

## Technical Notes

- Can use a simple Python script with `requests` + `time` or `locust` for load testing
- Run benchmark against Docker container for consistency
- Save results in a markdown file or as script output
- Before: current code loads model/CSV on every request (~200-500ms per request)
- After: preloaded resources should bring it down to ~10-50ms per request

## Files to Create

- `benchmarks/latency_test.py` — benchmark script
- `benchmarks/results.md` — documented results (optional)
