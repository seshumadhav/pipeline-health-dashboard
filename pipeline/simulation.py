import time
import random
from typing import List

from pipeline.models import SignalEvent, Stage, SIGNAL_TYPE_DESCRIPTIONS
from pipeline.event_logger import (
    log_event_enqueued,
    log_event_processed,
    set_event_logging,
)


def create_ingest_stage() -> Stage:
    """
    Create the ingest stage for the pipeline.
    """
    return Stage(
        name="ingest",
        capacity_per_tick=100,
        base_latency_ms=1.0,
        jitter_ms=0.2,
    )


def generate_events(count: int) -> List[SignalEvent]:
    """
    Generate a mixed stream of signal events.
    """
    now = time.time()
    signal_types = list(SIGNAL_TYPE_DESCRIPTIONS.keys())

    return [
        SignalEvent(
            id=int(now * 1000) + i,
            signal_type=random.choice(signal_types),
        )
        for i in range(count)
    ]


def run_single_tick(
    stage: Stage,
    incoming_events: List[SignalEvent],
    *,
    log_events: bool = True,
    enforce_queue_invariant: bool = True,
) -> None:
    """
    Simulate a single processing tick for one pipeline stage.
    """

    set_event_logging(log_events)

    # --- Domain sanity ---
    for event in incoming_events:
        assert event.signal_type in SIGNAL_TYPE_DESCRIPTIONS, (
            f"Unknown signal type: {event.signal_type}"
        )

    # Enqueue
    for event in incoming_events:
        stage.enqueue(event)
        log_event_enqueued(stage, event)

    stage.record_queue_depth()

    effective_capacity = int(stage.capacity_per_tick / stage.slowdown_factor)

    processed = 0
    while stage.queue and processed < effective_capacity:
        event = stage.queue.popleft()
        processed += 1

        latency_ms = max(
            0.0,
            random.uniform(
                stage.base_latency_ms - stage.jitter_ms,
                stage.base_latency_ms + stage.jitter_ms,
            ),
        )

        stage.metrics.record_latency(latency_ms)
        log_event_processed(stage, event)

    # --- Capacity invariant ---
    assert processed <= effective_capacity, (
        f"Processed {processed} events, exceeding effective capacity "
        f"{effective_capacity} for stage {stage.name}"
    )

    stage.metrics.processed += processed

    # --- Queue invariant (single-stage ONLY) ---
    if enforce_queue_invariant:
        expected_remaining = max(
            0, len(incoming_events) - stage.capacity_per_tick
        )
        assert len(stage.queue) == expected_remaining, (
            f"Queue size mismatch: expected {expected_remaining}, "
            f"got {len(stage.queue)}"
        )
