import logging
from pipeline.models import SignalEvent, Stage

# Configure logging to write to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='pipeline_events.log',
    filemode='a'
)

logger = logging.getLogger(__name__)


def log_event_enqueued(stage: Stage, event: SignalEvent) -> None:
    """
    Log when an event is enqueued to a stage.
    """
    logger.info(
        f"Event enqueued - Stage: {stage.name}, Event ID: {event.id}, "
        f"Signal Type: {event.signal_type}"
    )


def log_event_processed(stage: Stage, event: SignalEvent) -> None:
    """
    Log when an event is processed by a stage.
    """
    logger.info(
        f"Event processed - Stage: {stage.name}, Event ID: {event.id}, "
        f"Signal Type: {event.signal_type}"
    )
