import random
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
import argparse
import time

# Default server URL
SERVER_URL = "http://127.0.0.1:8080"

# Global metrics
stress_test_metrics = {
    "success": 0,
    "failed": 0,
    "rejected": 0,
    "response_times": []
}

metrics_lock = threading.Lock()

def record_metric(key, response_time=None):
    """Thread-safe recording of metrics."""
    with metrics_lock:
        if key in stress_test_metrics:
            stress_test_metrics[key] += 1
        if response_time is not None:
            stress_test_metrics["response_times"].append(response_time)

def make_request(url, fail_mode=None):
    """
    Makes a single HTTP GET request to the server.
    Categorizes server responses as 'success', 'failed', or 'rejected'.
    """
    start_time = time.time()
    try:
        if fail_mode == 'timeout':
            response = requests.get(url, timeout=0.001)
        elif fail_mode == 'connection_error':
            raise requests.ConnectionError("Simulated connection error")
        elif fail_mode == 'random_error':
            if random.choice([True, False]):
                response = requests.get(url, timeout=0.001)
            else:
                raise requests.ConnectionError("Simulated connection error")
        else:
            response = requests.get(url)

        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            record_metric("success", elapsed_time)
        else:
            record_metric("failed")
    except requests.Timeout:
        record_metric("failed")
    except requests.ConnectionError:
        record_metric("rejected")
    except Exception:
        record_metric("failed")

def toggle_cache(url):
    """Send a request to toggle the cache on the server."""
    try:
        response = requests.get(f"{url}/toggle_cache")
        print(f"Cache toggle response: {response.text}")
    except Exception as e:
        print(f"Failed to toggle cache: {e}")

def stress_test(url, num_requests, fail_mode=None, max_threads=10, delay=0):
    """Runs a stress test on the server with specified failure mode."""
    with ThreadPoolExecutor(max_threads) as executor:
        for _ in range(num_requests):
            executor.submit(make_request, url, fail_mode)
            if delay > 0:
                time.sleep(delay)

    print("\n--- Stress Test Metrics ---")
    total_requests = sum(value for key, value in stress_test_metrics.items() if key != "response_times")
    print(f"Total Requests: {total_requests}")
    for key in ["success", "failed", "rejected"]:
        print(f"{key.capitalize()}: {stress_test_metrics[key]}")
    if stress_test_metrics["response_times"]:
        avg_response_time = sum(stress_test_metrics["response_times"]) / len(stress_test_metrics["response_times"])
        print(f"Average Response Time: {avg_response_time:.2f}s")

def main():
    parser = argparse.ArgumentParser(description="Stress Test for HTTP Server")
    parser.add_argument("--url", type=str, help="Server URL", default=SERVER_URL)
    parser.add_argument("--requests", type=int, help="Number of concurrent requests", default=50)
    parser.add_argument("--fail", type=str, choices=['timeout', 'connection_error', 'random_error'], help="Simulate failure mode")
    parser.add_argument("--threads", type=int, help="Max threads in thread pool", default=10)
    parser.add_argument("--delay", type=float, help="Delay (in seconds) between requests", default=0)
    parser.add_argument("--toggle_cache", action="store_true", help="Toggle server cache before the test")
    args = parser.parse_args()

    if args.toggle_cache:
        toggle_cache(args.url)

    print(f"Starting stress test with {args.requests} requests to {args.url}")
    if args.fail:
        print(f"Simulating failure mode: {args.fail}")
    if args.delay > 0:
        print(f"Adding a delay of {args.delay} seconds between requests.")

    stress_test(
        url=args.url,
        num_requests=args.requests,
        fail_mode=args.fail,
        max_threads=args.threads,
        delay=args.delay
    )
    print("\nStress test completed.")

if __name__ == "__main__":
    main()
