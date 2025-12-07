import time

from pipeline.models import Stage
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


def run_live_simulation(ticks: int = 10) -> None:
    pipeline = create_pipeline()

    for tick in range(1, ticks + 1):
        print(f"\nTICK {tick}", flush=True)
        print("----------------------------------------", flush=True)

        # Simulate enrichment degradation starting at tick 4
        # (e.g., heavier ML inference, slower API, costlier analytical query)
        if tick >= 4:
            for stage in pipeline.stages:
                if stage.name == "enrich":
                    stage.slowdown_factor = 2.5

        incoming_events = generate_events(200)
        pipeline.tick(incoming_events)

        for stage in pipeline.stages:
            render_dashboard(stage)
            print()

        time.sleep(0.4)  # slow enough for humans to watch


if __name__ == "__main__":
    run_live_simulation()
