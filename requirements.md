# Pipeline Health Dashboard

## Objective

Model a data pipeline to demonstrate an opinionated view of how I think about running operations day to day on an analytics pipeline.

## Desired Outcomes

This prototype demonstrates:

- **Production operations mindset** - not just building features, but keeping systems running
- **Observability expertise** - knowing what to measure and how to visualize it  
- **Incident response readiness** - detecting and diagnosing problems quickly
- **Business impact awareness** - connecting technical metrics to business outcomes
- **Operational maturity** - proactive monitoring, SLO tracking, and systematic incident management

## Non-Goals

This prototype explicitly does NOT aim to:

- **Build production-ready infrastructure** - this is a demonstration, not enterprise software
- **Implement comprehensive data processing** - signal processing is simulated, not real
- **Create a full monitoring stack** - no persistent storage, alerting systems, or dashboards
- **Handle real data volumes** - optimized for demonstration clarity, not performance
- **Provide complete incident management** - shows detection and diagnosis, not full remediation workflows
- **Replace existing monitoring tools** - this is educational/interview material, not a product

## What This Prototype Does

### 1. Real-World Pipeline Simulation

- **Simulates a data processing pipeline** that handles business signals (sales data, field reports, market trends)
- **Models realistic bottlenecks** where one stage (enrichment) can't keep up with incoming data
- **Shows what happens** when systems get overwhelmed and how they recover

### 2. Health Monitoring Dashboard

- **Live dashboard** that updates every few seconds showing system health
- **Traffic light system**: Green = healthy, Orange = degraded, Red = critical
- **Key metrics displayed**: How many events processed, queue backlogs, processing speeds
- **Signal breakdown**: What types of business data are flowing through

### 3. Service Level Agreement (SLO) Tracking

- **Measures critical performance targets**:
  - "Can we process data end-to-end within 10 time units?" (latency SLO)
  - "Are we processing at least 35 events per cycle?" (throughput SLO)
- **Pass/Fail indicators** show when systems meet or miss targets
- **Real-time alerting** when performance degrades

### 4. Incident Detection & Response

- **Automatically detects problems** like queue overflows or missed performance targets
- **Provides clear incident summaries** showing exactly what went wrong
- **Shows operational maturity** through proactive monitoring vs reactive firefighting

### 5. Human-in-the-Loop Quality Control

- **Randomly samples 0.5-2% of events** for manual review
- **Shows which specific data points** need human inspection
- **Demonstrates understanding** that automation isn't 100% - humans still needed

### 6. Realistic Operational Patterns

- **Traffic varies randomly** (quiet periods, busy periods, sudden spikes)
- **Systems occasionally degrade** (like when ML models slow down or APIs get sluggish)  
- **Recovery happens automatically** after problems resolve
- **Shows resilience thinking** - how systems behave under stress

## Dependencies

- **Python 3.8+** standard library only
- **No external packages required**

## FAQ

### Why build this at all?

I wanted a concrete way to show how I think about day-to-day operations — not just is the system healthy now, but how it trends toward failure and where pressure shows up first.

### Why keep it so simple?

Because the hard part isn't concurrency or tooling — it's choosing the right signals and contracts early. I wanted the core dynamics to be obvious before adding realism.

### Why these signal types?

They map to three realities analytics platforms deal with: what happened (sales activity), what the field is seeing (field interaction), and broader context (market signals). The pipeline treats them the same for now; the distinction matters later for diagnosis and prioritization.

### How would this evolve?

Next steps would be latency sampling, tail metrics, then stage-specific failure modes and backpressure. Only after that would I introduce persistence or real tooling.

### Why tools were not used?

I haven't owned ClickHouse or dbt recently, but the mental model doesn't change: capacity, backpressure, tail latency, and correctness. Tooling is a ramp; operational instincts aren't. That's why I focused the prototype on fundamentals, not vendor choice.