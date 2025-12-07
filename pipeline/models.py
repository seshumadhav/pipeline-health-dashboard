from dataclasses import dataclass, field
from typing import Deque, List
from collections import deque
import time


@dataclass
class Event:
    """
    Represents a unit of work flowing through the pipeline.

    An Event is created at ingestion time and moves through each
    pipeline stage (ingest → normalize → enrich → store → serve).

    Conceptually, an event could represent:
      - a point-of-sale signal
      - a field sales interaction
      - a social or market signal tied to a product, brand, or region
      - a derived analytical observation used for downstream insights

    This class intentionally keeps the event structure minimal.
    In real systems, the payload would vary by use case and evolve
    over time as the platform matures.

    Example (illustrative only):
        >>> event = Event(id=987654)
        >>> event.id
        987654
        >>> isinstance(event.created_at, float)
        True

        # Conceptual payload example (not modeled here):
        # {
        #   "brand": "Example Spirits Co.",
        #   "product": "Premium Vodka",
        #   "location": "Austin, TX",
        #   "signal_type": "sales_activity",
        #   "timestamp": "2025-01-03T18:42:11Z"
        # }
    """
    id: int
    created_at: float = field(default_factory=time.time)


@dataclass
class StageMetrics:
    """
    Metrics collected for a pipeline stage over time.

    These metrics are intentionally simple, but they are the
    leading indicators for operational health in data platforms:
      - throughput degradation
      - tail-latency creep
      - queue buildup and backpressure
      - silent correctness risks

    In analytics systems, issues at this layer often surface
    indirectly as:
      - delayed dashboards
      - stale insights
      - inconsistent regional or product-level reporting
      - loss of trust from downstream consumers

    Example:
        >>> metrics = StageMetrics()
        >>> metrics.processed
        0
        >>> metrics.latencies_ms.append(18.2)
        >>> metrics.queue_depths.append(7)
        >>> metrics.errors
        0
    """
    processed: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    queue_depths: List[int] = field(default_factory=list)
    errors: int = 0


@dataclass
class Stage:
    """
    Represents a pipeline stage such as ingest, normalize, enrich,
    store, or serve.

    Each stage models a real operational boundary in a data platform:
      - ingest: accepting external signals
      - normalize: cleaning and standardizing inputs
      - enrich: joining with reference or contextual data
      - store: persisting analytical representations
      - serve: powering downstream APIs, dashboards, or exports

    The goal is not to mimic a specific implementation, but to
    capture the universal dynamics that cause data pipelines
    to succeed or fail: capacity limits, latency variance,
    queue buildup, and partial degradation.

    Example:
        >>> stage = Stage(
        ...     name="enrich",
        ...     capacity_per_tick=500,
        ...     base_latency_ms=8.0,
        ...     jitter_ms=4.0
        ... )
        >>> stage.name
        'enrich'
        >>> stage.capacity_per_tick
        500
        >>> len(stage.queue)
        0
    """
    name: str
    capacity_per_tick: int
    base_latency_ms: float
    jitter_ms: float

    queue: Deque[Event] = field(default_factory=deque)
    metrics: StageMetrics = field(default_factory=StageMetrics)

    def enqueue(self, event: Event) -> None:
        """
        Add an event to the stage's processing queue.
        """
        self.queue.append(event)

    def record_queue_depth(self) -> None:
        """
        Record the current queue depth for observability.
        """
        self.metrics.queue_depths.append(len(self.queue))
