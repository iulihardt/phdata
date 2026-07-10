============================================================
  Benchmark: 100 requests to POST /predict
============================================================

Warmup (1 request)...
  Warmup: 79.9 ms

Single request test...
  Response: {'predicted_price': 518190.0}
  Latency:  13.8 ms

Load test (100 requests)...
  [ 10.0%] 10/100 done
  [ 20.0%] 20/100 done
  [ 30.0%] 30/100 done
  [ 40.0%] 40/100 done
  [ 50.0%] 50/100 done
  [ 60.0%] 60/100 done
  [ 70.0%] 70/100 done
  [ 80.0%] 80/100 done
  [ 90.0%] 90/100 done
  [100.0%] 100/100 done

============================================================
  RESULTS
============================================================
  Requests:    100 total, 0 errors
  Total time:  0.94 s
  Throughput:  106.2 req/s

  Latency (ms):
    Min:         8.5
    Mean:        9.4
    Median:      9.3
    p95:        10.4
    p99:        12.5
    Max:        12.5
    Stdev:       0.6

    ============================================================
    ============================================================
    ============================================================
    (ia_env) iulihardt@MacBook-Air-2 phdata-mle-project-challenge-2026-22ec952f6305 % python test/benchmark_api.py -n 3000

============================================================
  Benchmark: 3000 requests to POST /predict
============================================================

Warmup (1 request)...
  Warmup: 28.3 ms

Single request test...
  Response: {'predicted_price': 518190.0}
  Latency:  11.9 ms

Load test (3000 requests)...
  [ 10.0%] 300/3000 done
  [ 20.0%] 600/3000 done
  [ 30.0%] 900/3000 done
  [ 40.0%] 1200/3000 done
  [ 50.0%] 1500/3000 done
  [ 60.0%] 1800/3000 done
  [ 70.0%] 2100/3000 done
  [ 80.0%] 2400/3000 done
  [ 90.0%] 2700/3000 done
  [100.0%] 3000/3000 done

============================================================
  RESULTS
============================================================
  Requests:    3000 total, 0 errors
  Total time:  27.54 s
  Throughput:  108.9 req/s

  Latency (ms):
    Min:         8.0
    Mean:        9.1
    Median:      8.9
    p95:        10.0
    p99:        11.0
    Max:        49.2
    Stdev:       1.3
============================================================