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
        self.current_tick = 0

    def tick(self, incoming_events: List[SignalEvent]) -> None:
        """
        Run a single tick through all stages.
        Events flow between stages with a 1-tick delay (realistic processing time).
        Backpressure naturally propagates via queue buildup.
        """
        self.current_tick += 1
        
        # Stamp ingestion tick on incoming events
        for event in incoming_events:
            event.ingestion_tick = self.current_tick
        
        # Capture output buffers from PREVIOUS tick before processing
        prev_tick_outputs = [stage.output_buffer.copy() for stage in self.stages]
        
        # First stage gets fresh incoming events
        stage_inputs = incoming_events

        for i, stage in enumerate(self.stages):
            # Process this stage with its input events
            run_single_tick(
                stage,
                stage_inputs,
                log_events=False,
                enforce_queue_invariant=False,
                current_tick=self.current_tick,
            )
            
            # Next stage gets previous stage's output from PREVIOUS tick (captured before processing)
            # This enforces minimum 1-tick processing delay per stage
            if i + 1 < len(self.stages):
                stage_inputs = prev_tick_outputs[i]
            else:
                # Last stage (store) - no next stage
                stage_inputs = []
