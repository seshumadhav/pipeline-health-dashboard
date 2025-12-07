import logging
from pipeline.models import SignalEvent, Stage

"""
Event-level logging for debugging and prototyping.

By default, event logging is ENABLED and logs are written to a file.
This is intentionally verbose and suitable for demos and small simulations.

In real systems, this would typically be sampled, aggregated,
or replaced with metrics and tracing.
"""

# --- Configuration flag ---
LOG_EVENTS: bool = True


def set_event_logging(enabled: bool) -> None:
    """
    Enable or disable event-level logging.

    Intended to be called by the simulation or CLI.
    """
    global LOG_EVENTS
    LOG_EVENTS = enabled


# --- Logging configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="pipeline_events.log",
    filemode="a",
)

logger = logging.getLogger(__name__)


def log_event_enqueued(stage: Stage, event: SignalEvent) -> None:
    """
    Log when an event is enqueued to a stage.
    """
    if not LOG_EVENTS:
        return

    logger.info(
        f"Event enqueued - Stage: {stage.name}, "
        f"Event ID: {event.id}, Signal Type: {event.signal_type}"
    )


def log_event_processed(stage: Stage, event: SignalEvent) -> None:
    """
    Log when an event is processed by a stage.
    """
    if not LOG_EVENTS:
        return

    logger.info(
        f"Event processed - Stage: {stage.name}, "
        f"Event ID: {event.id}, Signal Type: {event.signal_type}"
    )
