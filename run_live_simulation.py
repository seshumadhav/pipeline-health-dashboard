import time

from pipeline.models import Stage, compute_percentile
from pipeline.pipeline_chain import StageChain
from pipeline.simulation import generate_events
from pipeline.dashboard import render_dashboard


def create_pipeline() -> StageChain:
    return StageChain([
        Stage("ingest", capacity_per_tick=100, base_latency_ms=1.0, jitter_ms=0.2),
        Stage("normalize", capacity_per_tick=80, base_latency_ms=2.5, jitter_ms=0.5),
        Stage("enrich", capacity_per_tick=50, base_latency_ms=3.0, jitter_ms=0.7),
        Stage("store", capacity_per_tick=60, base_latency_ms=1.0, jitter_ms=0.2),
    ])


def print_incident_summary(pipeline: StageChain) -> None:
    """
    Print a brief operational summary showing degradation impact.
    """
    print("\n" + "=" * 60)
    print("INCIDENT SUMMARY")
    print("=" * 60)
    
    enrich_stage = next(s for s in pipeline.stages if s.name == "enrich")
    
    if enrich_stage.slowdown_factor > 1.0:
        print(f"Bottleneck: {enrich_stage.name} stage (slowdown factor: {enrich_stage.slowdown_factor}x)")
        print(f"  Effective capacity reduced from 50 to ~{int(50/enrich_stage.slowdown_factor)} events/tick")
    else:
        print(f"Stage: {enrich_stage.name} (slowdown factor: {enrich_stage.slowdown_factor}x - no slowdown)")
    
    print(f"  Final queue depth: {len(enrich_stage.queue)} events")
    
    if enrich_stage.metrics.latencies_ms:
        p95 = compute_percentile(enrich_stage.metrics.latencies_ms, 0.95)
        p99 = compute_percentile(enrich_stage.metrics.latencies_ms, 0.99)
        print(f"  Latency p95/p99: {p95:.2f}/{p99:.2f} ms")
    
    print("Backpressure propagation:")
    for stage in pipeline.stages:
        if stage.name != "enrich":
            print(f"  {stage.name}: queue depth = {len(stage.queue)}")
    
    print("=" * 60)


def render_tick_table(pipeline: StageChain) -> None:
    """
    Render pipeline health as a compact table.
    """
    from collections import Counter
    
    stages = pipeline.stages
    
    # Header
    print()
    print("=" * 95)
    header = f"{'Metric':<25} | {'INGEST':<12} | {'NORMALIZE':<12} | {'ENRICH':<12} | {'STORE':<12}"
    print(header)
    print("-" * 95)
    
    # Processed
    values = [str(stage.metrics.processed) for stage in stages]
    print(f"{'Processed':<25} | {values[0]:<12} | {values[1]:<12} | {values[2]:<12} | {values[3]:<12}")
    
    # Queue depth
    values = [str(stage.metrics.queue_depths[-1] if stage.metrics.queue_depths else 0) for stage in stages]
    print(f"{'Queue depth':<25} | {values[0]:<12} | {values[1]:<12} | {values[2]:<12} | {values[3]:<12}")
    
    # Latency category header
    print(f"{'Latency':<25} | {'':<12} | {'':<12} | {'':<12} | {'':<12}")
    
    # Latency p50
    values = []
    for stage in stages:
        if stage.metrics.latencies_ms:
            p50 = compute_percentile(stage.metrics.latencies_ms, 0.50)
            values.append(f"{p50:.2f}")
        else:
            values.append("-")
    print(f"{'  p50 (ms)':<25} | {values[0]:<12} | {values[1]:<12} | {values[2]:<12} | {values[3]:<12}")
    
    # Latency p95
    values = []
    for stage in stages:
        if stage.metrics.latencies_ms:
            p95 = compute_percentile(stage.metrics.latencies_ms, 0.95)
            values.append(f"{p95:.2f}")
        else:
            values.append("-")
    print(f"{'  p95 (ms)':<25} | {values[0]:<12} | {values[1]:<12} | {values[2]:<12} | {values[3]:<12}")
    
    # Latency p99
    values = []
    for stage in stages:
        if stage.metrics.latencies_ms:
            p99 = compute_percentile(stage.metrics.latencies_ms, 0.99)
            values.append(f"{p99:.2f}")
        else:
            values.append("-")
    print(f"{'  p99 (ms)':<25} | {values[0]:<12} | {values[1]:<12} | {values[2]:<12} | {values[3]:<12}")
    
    # Signals category header
    print(f"{'Signals':<25} | {'':<12} | {'':<12} | {'':<12} | {'':<12}")
    
    # Signal types
    for signal_type in ["field_interaction", "market_signal", "sales_activity"]:
        values = []
        for stage in stages:
            if stage.queue:
                type_counts = Counter(e.signal_type for e in stage.queue)
                count = type_counts.get(signal_type, 0)
                values.append(str(count))
            else:
                values.append("0")
        print(f"{'  ' + signal_type:<25} | {values[0]:<12} | {values[1]:<12} | {values[2]:<12} | {values[3]:<12}")
    
    print("=" * 95)
    
    # SLO Metrics Table
    print()
    print("=" * 95)
    print("SLO METRICS")
    print("-" * 95)
    
    # SLO 1: End-to-end latency p95 < 10ms
    e2e_latencies = []
    for stage in stages:
        e2e_latencies.extend(stage.metrics.latencies_ms)
    if e2e_latencies:
        e2e_p95 = compute_percentile(e2e_latencies, 0.95)
        slo_status = "✓ PASS" if e2e_p95 < 10.0 else "✗ FAIL"
        print(f"{'End-to-end p95 latency':<40} | {e2e_p95:>8.2f} ms | Target: < 10ms | {slo_status}")
    else:
        print(f"{'End-to-end p95 latency':<40} | {'N/A':>8} | Target: < 10ms | -")
    
    # SLO 2: Max queue depth < 100 events
    max_queue = max(len(stage.queue) for stage in stages)
    slo_status = "✓ PASS" if max_queue < 100 else "✗ FAIL"
    print(f"{'Max queue depth':<40} | {max_queue:>8} events | Target: < 100 | {slo_status}")
    
    # SLO 3: Pipeline throughput > 150 events/tick
    total_processed = sum(stage.metrics.processed for stage in stages)
    slo_status = "✓ PASS" if total_processed > 150 else "✗ FAIL"
    print(f"{'Total throughput':<40} | {total_processed:>8} events | Target: > 150 | {slo_status}")
    
    print("=" * 95)


def run_live_simulation(ticks: int = 10) -> None:
    pipeline = create_pipeline()

    for tick in range(1, ticks + 1):
        print(f"\nTICK {tick}", flush=True)

        # Simulate enrichment degradation starting at tick 4
        # (e.g., heavier ML inference, slower API, costlier analytical query)
        if tick >= 4:
            for stage in pipeline.stages:
                if stage.name == "enrich":
                    stage.slowdown_factor = 2.5

        incoming_events = generate_events(200)
        pipeline.tick(incoming_events)

        render_tick_table(pipeline)

        time.sleep(0.4)  # slow enough for humans to watch
    
    # Print incident summary after simulation completes
    print_incident_summary(pipeline)


if __name__ == "__main__":
    run_live_simulation()
