import requests
import time
import argparse
import statistics

URL = "http://localhost:8000/predict"

PAYLOAD = {
    "bedrooms": 3,
    "bathrooms": 2.5,
    "sqft_living": 2000,
    "sqft_lot": 5000,
    "floors": 2,
    "sqft_above": 1500,
    "sqft_basement": 500,
    "zipcode": "98125",
}


def single_request():
    start = time.perf_counter()
    resp = requests.post(URL, json=PAYLOAD)
    elapsed = (time.perf_counter() - start) * 1000
    resp.raise_for_status()
    return elapsed, resp.json()


def run_benchmark(n: int):
    print(f"\n{'='*60}")
    print(f"  Benchmark: {n} requests to POST /predict")
    print(f"{'='*60}\n")

    # Warmup
    print("Warmup (1 request)...")
    warmup_ms, _ = single_request()
    print(f"  Warmup: {warmup_ms:.1f} ms\n")

    # Single request test
    print("Single request test...")
    single_ms, result = single_request()
    print(f"  Response: {result}")
    print(f"  Latency:  {single_ms:.1f} ms\n")

    # Load test
    print(f"Load test ({n} requests)...")
    latencies = []
    errors = 0
    total_start = time.perf_counter()

    for i in range(n):
        try:
            ms, _ = single_request()
            latencies.append(ms)
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  Error on request {i+1}: {e}")

        if (i + 1) % max(1, n // 10) == 0:
            pct = (i + 1) / n * 100
            print(f"  [{pct:5.1f}%] {i+1}/{n} done")

    total_elapsed = time.perf_counter() - total_start

    # Results
    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  Requests:    {n} total, {errors} errors")
    print(f"  Total time:  {total_elapsed:.2f} s")
    print(f"  Throughput:  {n / total_elapsed:.1f} req/s")
    print()
    print(f"  Latency (ms):")
    print(f"    Min:    {min(latencies):8.1f}")
    print(f"    Mean:   {statistics.mean(latencies):8.1f}")
    print(f"    Median: {p50:8.1f}")
    print(f"    p95:    {p95:8.1f}")
    print(f"    p99:    {p99:8.1f}")
    print(f"    Max:    {max(latencies):8.1f}")
    print(f"    Stdev:  {statistics.stdev(latencies):8.1f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark the /predict API")
    parser.add_argument("-n", type=int, default=100, help="Number of requests (default: 100)")
    args = parser.parse_args()
    run_benchmark(args.n)
