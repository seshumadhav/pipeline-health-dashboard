from dataclasses import dataclass, field
from typing import Deque, List, Dict
from collections import deque
import time


# Domain-level reference for signal semantics.
# This is illustrative and intentionally technology-agnostic.
SIGNAL_TYPE_DESCRIPTIONS: Dict[str, str] = {
    "sales_activity": (
        "Direct commercial or transactional signals reflecting sales execution. "
        "Examples include: "
        "1) a distributor order placed or updated for a specific SKU, "
        "2) point-of-sale movement showing units sold at a retail location."
    ),
    "field_interaction": (
        "Qualitative or semi-structured observations captured from the field. "
        "Examples include: "
        "1) sales rep notes or store feedback after a visit, "
        "2) compliance checks such as display presence or planogram adherence."
    ),
    "market_signal": (
        "External or aggregated indicators describing broader market conditions. "
        "Examples include: "
        "1) category-level trends (e.g., premium spirits growth in a region), "
        "2) competitive activity such as rival promotions or pricing changes."
    ),
}


@dataclass
class SignalEvent:
    """
    Represents a unit of signal flowing through the pipeline.

    A SignalEvent is created at ingestion time and moves through each
    pipeline stage (ingest → normalize → enrich → store → serve).

    signal_type indicates the semantic nature of the signal.
    See SIGNAL_TYPE_DESCRIPTIONS for illustrative meanings and examples.

    Example:
        >>> event = SignalEvent(id=123, signal_type="sales_activity")
        >>> event.signal_type
        'sales_activity'
    """
    id: int
    signal_type: str
    created_at: float = field(default_factory=time.time)


@dataclass
class StageMetrics:
    """
    Metrics collected for a pipeline stage over time.

    These metrics surface early indicators of operational health:
      - throughput degradation
      - tail-latency creep
      - queue buildup
      - correctness risks
    """
    processed: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    queue_depths: List[int] = field(default_factory=list)
    errors: int = 0


@dataclass
class Stage:
    """
    Represents a pipeline stage such as ingest, normalize, enrich, store, or serve.

    Each stage models a real operational boundary where capacity limits,
    latency variance, and partial failures can emerge.
    """
    name: str
    capacity_per_tick: int
    base_latency_ms: float
    jitter_ms: float

    queue: Deque[SignalEvent] = field(default_factory=deque)
    metrics: StageMetrics = field(default_factory=StageMetrics)

    def enqueue(self, event: SignalEvent) -> None:
        """
        Add an event to the stage's processing queue.
        """
        self.queue.append(event)

    def record_queue_depth(self) -> None:
        """
        Record the current queue depth for observability.
        """
        self.metrics.queue_depths.append(len(self.queue))
