"""
High-Concurrency Stress Test & SQLite Lock Contention Simulator.
Simulates 1,000+ requests across 50 concurrent threads to evaluate:
1. SQLite WAL mode resilience and lock contention under read/write bursts.
2. Endpoint throughput, error rate (0% tolerance for 500s or lock errors), and latency distribution.
3. System stability under heavy load.
"""

import time
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

# Add workspace root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding="utf-8")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stock_agent_django.settings")
import django
django.setup()

from django.test import Client
from apps.market.models import Stock


def simulate_user_request(user_id: int, request_type: str) -> dict:
    """Simulates a single user action on the platform."""
    client = Client()
    start_time = time.time()
    endpoint = ""
    status_code = None

    try:
        if request_type == "pulse":
            endpoint = "/api/market/pulse/"
            res = client.get(endpoint)
            status_code = res.status_code
        elif request_type == "rankings":
            endpoint = "/rankings/"
            res = client.get(endpoint)
            status_code = res.status_code
        elif request_type == "search":
            endpoint = "/api/search/?q=tata"
            res = client.get(endpoint)
            status_code = res.status_code
        elif request_type == "ipo_list":
            endpoint = "/ipo/api/list/"
            res = client.get(endpoint)
            status_code = res.status_code
        elif request_type == "research_page":
            endpoint = "/research/TCS.NS/"
            res = client.get(endpoint)
            status_code = res.status_code
        elif request_type == "portfolio_analysis":
            endpoint = "/portfolio/analysis/"
            res = client.get(endpoint)
            status_code = res.status_code
        elif request_type == "db_write_burst":
            # Concurrent database write simulation (touch updated_at)
            stock = Stock.objects.first()
            if stock:
                stock.save(update_fields=['updated_at'])
            status_code = 200
            endpoint = "db_write_direct"

        duration = time.time() - start_time
        return {
            "user_id": user_id,
            "request_type": request_type,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": duration * 1000.0,
            "error": None
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            "user_id": user_id,
            "request_type": request_type,
            "endpoint": endpoint,
            "status_code": 500,
            "duration_ms": duration * 1000.0,
            "error": str(e)
        }


def run_load_simulation(total_requests: int = 1000, max_workers: int = 50):
    print("=" * 70)
    print(f"INITIATING LOAD SIMULATION: {total_requests} REQUESTS ACROSS {max_workers} WORKERS")
    print("=" * 70)

    request_types = [
        "pulse", "rankings", "search", "ipo_list",
        "research_page", "portfolio_analysis", "db_write_burst"
    ]

    tasks = []
    overall_start = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(total_requests):
            req_type = request_types[i % len(request_types)]
            tasks.append(executor.submit(simulate_user_request, i, req_type))

        results = []
        for future in as_completed(tasks):
            results.append(future.result())

    overall_duration = time.time() - overall_start

    # Metrics aggregation
    status_counts = Counter(r["status_code"] for r in results)
    errors = [r for r in results if r["error"] is not None]
    durations = [r["duration_ms"] for r in results]
    avg_latency = sum(durations) / len(durations) if durations else 0
    p95_latency = sorted(durations)[int(len(durations) * 0.95)] if durations else 0
    rps = total_requests / overall_duration if overall_duration > 0 else 0

    print("\n--- PERFORMANCE & STRESS TEST RESULTS ---")
    print(f"Total Requests Completed : {len(results)}")
    print(f"Total Time Elapsed       : {overall_duration:.2f} seconds")
    print(f"Throughput (RPS)         : {rps:.1f} req/sec")
    print(f"Average Latency          : {avg_latency:.2f} ms")
    print(f"95th Percentile Latency  : {p95_latency:.2f} ms")
    print(f"Status Code Breakdown    : {dict(status_counts)}")
    print(f"Database Lock Errors     : {len([e for e in errors if 'locked' in str(e['error']).lower()])}")
    print(f"Total Failures           : {len(errors)}")

    if errors:
        print("\nSample Errors Encountered:")
        for err in errors[:5]:
            print(f"  - [{err['request_type']}] {err['error']}")

    assert len(errors) == 0, f"Expected 0 errors under load, got {len(errors)}"
    assert status_counts.get(200, 0) == total_requests, f"Expected {total_requests} HTTP 200 OKs, got {status_counts}"
    print("\n[SUCCESS] 100% OF REQUESTS RETURNED HTTP 200 OK (0 LOCKS, 0 ERRORS)!")
    print("=" * 70)


if __name__ == "__main__":
    run_load_simulation(total_requests=1000, max_workers=50)
