import time
import random
from typing import List

from pipeline.models import SignalEvent, Stage, SIGNAL_TYPE_DESCRIPTIONS
from pipeline.event_logger import log_event_enqueued, log_event_processed


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

    Signal types are illustrative and domain-relevant:
      - sales_activity
      - field_interaction
      - market_signal
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


def run_single_tick(stage: Stage, incoming_events: List[SignalEvent]) -> None:
    """
    Simulate a single processing tick for one pipeline stage.

    - enqueue incoming events
    - process up to stage capacity
    - record queue depth and processed count
    - enforce core invariants via sanity checks
    """

    # --- Domain sanity: signal types must be known ---
    for event in incoming_events:
        assert event.signal_type in SIGNAL_TYPE_DESCRIPTIONS, (
            f"Unknown signal type: {event.signal_type}"
        )

    # Enqueue all incoming events
    for event in incoming_events:
        stage.enqueue(event)
        log_event_enqueued(stage, event)

    stage.record_queue_depth()

    processed = 0
    while stage.queue and processed < stage.capacity_per_tick:
        event = stage.queue.popleft()
        processed += 1
        log_event_processed(stage, event)

    # --- Capacity invariant ---
    assert processed <= stage.capacity_per_tick, (
        f"Processed {processed} events, exceeding capacity "
        f"{stage.capacity_per_tick} for stage {stage.name}"
    )

    stage.metrics.processed += processed

    # --- Queue correctness invariant ---
    expected_remaining = max(0, len(incoming_events) - stage.capacity_per_tick)
    assert len(stage.queue) == expected_remaining, (
        f"Queue size mismatch: expected {expected_remaining}, "
        f"got {len(stage.queue)}"
    )

    # --- Metrics monotonicity ---
    assert stage.metrics.processed >= 0
