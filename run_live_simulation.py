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
    
    # Get store stage for end-to-end metrics
    store_stage = next(s for s in stages if s.name == "store")
    
    # SLO 1: End-to-end p95 processing time < 3 ticks
    if store_stage.metrics.e2e_processing_times:
        e2e_p95 = compute_percentile(store_stage.metrics.e2e_processing_times, 0.95)
        slo_status = "✓ PASS" if e2e_p95 < 3.0 else "✗ FAIL"
        print(f"{'E2E p95 processing time':<40} | {e2e_p95:>8.2f} ticks | Target: < 3 | {slo_status}")
    else:
        print(f"{'E2E p95 processing time':<40} | {'N/A':>11} | Target: < 3 | -")
    
    # SLO 2: Store stage throughput > 40 events/tick
    store_processed_this_tick = store_stage.metrics.processed if hasattr(store_stage.metrics, '_tick_processed') else 0
    # Use incremental processed count - track last tick's cumulative
    if not hasattr(pipeline, '_last_store_processed'):
        pipeline._last_store_processed = 0
    current_throughput = store_stage.metrics.processed - pipeline._last_store_processed
    pipeline._last_store_processed = store_stage.metrics.processed
    
    slo_status = "✓ PASS" if current_throughput >= 40 else "✗ FAIL"
    print(f"{'Store throughput (this tick)':<40} | {current_throughput:>8} events | Target: ≥ 40 | {slo_status}")
    
    print("=" * 95)
    
    # Monitoring Metrics with Health Zones
    print()
    print("=" * 95)
    print("MONITORING METRICS - Queue Health")
    print("-" * 95)
    
    # Define zone thresholds per stage (based on capacity)
    zone_config = {
        "ingest": {"green": 50, "orange": 150},      # capacity 100
        "normalize": {"green": 40, "orange": 120},   # capacity 80
        "enrich": {"green": 25, "orange": 75},       # capacity 50
        "store": {"green": 30, "orange": 90},        # capacity 60
    }
    
    for stage in stages:
        queue_depth = len(stage.queue)
        thresholds = zone_config.get(stage.name, {"green": 50, "orange": 150})
        
        if queue_depth <= thresholds["green"]:
            health = "🟢 GREEN"
        elif queue_depth <= thresholds["orange"]:
            health = "🟠 ORANGE"
        else:
            health = "🔴 RED"
        
        print(f"{stage.name.upper():<12} | Queue: {queue_depth:>6} | Green: ≤{thresholds['green']:<3} | Orange: ≤{thresholds['orange']:<3} | {health}")
    
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
