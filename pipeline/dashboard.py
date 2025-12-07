from collections import Counter
from pipeline.models import compute_percentile


def render_dashboard(stage):
    print("Pipeline Health Dashboard")
    print("-" * 40)
    print(f"Stage: {stage.name}")
    print(f"Processed: {stage.metrics.processed}")
    print(
        f"Queue depth (latest): "
        f"{stage.metrics.queue_depths[-1] if stage.metrics.queue_depths else 0}"
    )

    if stage.metrics.latencies_ms:
        p50 = compute_percentile(stage.metrics.latencies_ms, 0.50)
        p95 = compute_percentile(stage.metrics.latencies_ms, 0.95)
        p99 = compute_percentile(stage.metrics.latencies_ms, 0.99)

        print(f"Latency p50/p95/p99 (ms): {p50:.2f}/{p95:.2f}/{p99:.2f}")

    if stage.queue:
        type_counts = Counter(e.signal_type for e in stage.queue)
        print("Signal types in queue:")
        for k, v in type_counts.items():
            print(f"  {k}: {v}")

    print("Status: OK")
