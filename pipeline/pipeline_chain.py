from typing import List
from pipeline.models import SignalEvent, Stage
from pipeline.simulation import run_single_tick


class StageChain:
    """
    Simple multi-stage pipeline:
    ingest -> normalize -> enrich -> store
    """

    def __init__(self, stages: List[Stage]):
        self.stages = stages

    def tick(self, incoming_events: List[SignalEvent]) -> None:
        """
        Run a single tick through all stages.
        Backpressure naturally propagates via queue buildup.
        """
        overflow = incoming_events

        for stage in self.stages:
            run_single_tick(
                stage,
                overflow,
                log_events=False,
                enforce_queue_invariant=False,
            )
            overflow = list(stage.queue)
