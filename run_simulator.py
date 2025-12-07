import traceback
import sys

from pipeline.simulation import (
    create_ingest_stage,
    generate_events,
    run_single_tick,
)


def log(msg: str) -> None:
    print(msg)


def run_all_checks() -> None:
    """
    Run a full end-to-end sanity validation of the pipeline simulation.

    Uses simple invariants instead of a heavy test framework.
    """

    # --------------------------
    # Test 1: Basic ingest flow
    # --------------------------
    TEST_NAME = "Basic ingest flow (capacity + queue invariants)"
    log(f"\nSimulation started")
    log(f"Running test: {TEST_NAME}")

    stage = create_ingest_stage()
    events = generate_events(120)

    log(f"120 events enqueued")

    run_single_tick(stage, events)

    log(f"{stage.metrics.processed} events processed")

    assert stage.metrics.processed == 100, "Processed count mismatch"
    assert len(stage.queue) == 20, "Queue length mismatch after processing"

    log(f"✅ Test passed: {TEST_NAME}")

    # --------------------------
    # Test 2: Logging OFF mode
    # --------------------------
    TEST_NAME = "Event logging disabled override"
    log(f"\nRunning test: {TEST_NAME}")

    stage_quiet = create_ingest_stage()
    events_quiet = generate_events(10)

    run_single_tick(stage_quiet, events_quiet, log_events=False)

    assert stage_quiet.metrics.processed == 10, "Logging OFF affected processing"

    log(f"✅ Test passed: {TEST_NAME}")

    # --------------------------
    # Test 3: Domain guardrail
    # --------------------------
    TEST_NAME = "Unknown signal type rejection"
    log(f"\nRunning test: {TEST_NAME}")

    try:
        bad_stage = create_ingest_stage()
        bad_event = generate_events(1)[0]
        bad_event.signal_type = "invalid_signal"

        run_single_tick(bad_stage, [bad_event])

        raise AssertionError("Invalid signal type was not rejected")
    except AssertionError:
        log(f"✅ Test passed: {TEST_NAME}")


def main() -> None:
    try:
        run_all_checks()
        log("\n✅ All tests passed. Pipeline is OK.")
        sys.exit(0)
    except Exception:
        log("\n❌ Some tests failed. Pipeline has code issues.")
        log("\n--- Failure details ---")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
