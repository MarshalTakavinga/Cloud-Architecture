# ADR-005: Store-and-Forward Priority Lanes and Separate Backfill Stream

**Status:** Approved
**Date:** Step 5 of the Case Study 4 pipeline

## Context

Every plant must buffer ≥ 72 hours of outbound data through WAN outages (NFR-1) with ≤ 0.01% telemetry loss (NFR-6). When a plant reconnects, the platform must absorb a backfill burst of up to 300,000 values/sec across the fleet **without delaying other plants' live data by more than 60 seconds** (NFR-4).

The realistic worst case is Ramos Arizpe: a 19-hour outage on a 50 Mbps link, leaving about 7 GB of backlog. Genealogy (ADR-004) and anomaly events are small but matter most. Bulk telemetry is large and time-tolerant once it is hours old.

## Decision

**At the edge: a four-lane priority outbox.** The outbox is durable and replicated across both edge nodes. The Cloud Bridge always drains the highest non-empty lane first:

| Lane | Contents | Drain policy |
|---|---|---|
| 1 — Genealogy | `GenealogyRecorded` | Always first. Tiny volume. |
| 2 — Alerts | `AnomalyDetected` (+ waveform snapshots), fleet health, deployment status | Immediately after genealogy |
| 3 — Live | Telemetry, features, and state events newer than the **live horizon** (default 5 minutes) | Continuous, uncapped |
| 4 — Backfill | Anything older than the live horizon that has not yet been acknowledged | Rate-capped per plant (default 40% of link bandwidth, configurable), and only while lanes 1–3 are empty |

When the WAN drops, data that is still in lane 3 when it ages past the live horizon is **moved to lane 4**. On reconnect, a plant therefore goes live within seconds, and its history trickles in behind.

**In the cloud: separate live and backfill streams.** The bridge tags every batch with its lane. Cloud Ingestion writes lanes 1–3 to the live and genealogy streams, and lane 4 to a **separate backfill stream**, which has its own partitions and consumers.

- The **hot path consumes live only.** Hours-old backfill is never scored as if it were current, and it never competes with other plants' live data for hot-path capacity.
- The **time-series store, analytical store, and OEE Service consume both.** Late data is placed by **source timestamp**, and affected OEE windows are restated and marked as restated.
- **Deduplication** on `(site, source, sequence)` makes a resend after a partial acknowledgement harmless.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **A single FIFO queue per plant.** Rejected. After a 19-hour outage the plant's first live data would sit behind about 45 minutes of backlog, so its own anomaly and predictive insights would run 45 minutes stale exactly when a machine may need attention. Genealogy would also queue behind bulk telemetry.
2. **Drop the oldest data when the buffer is full, and resume live.** Rejected. It violates NFR-6 by design and silently removes the period an investigation would most want to see.
3. **Send live data only and never backfill; the plant historian holds the history.** Rejected. Two plants have no historian, and cross-plant training and OEE would have permanent gaps around every outage.
4. **Backfill through the same cloud stream, with more cloud capacity.** Rejected. More capacity helps throughput but not ordering. The hot path would still process hours-old data as if it were current and raise stale "predictive" alerts, and one plant's burst would still contend with everyone else's live traffic.

## Consequences

- **Positive:** NFR-4 is met structurally, not by over-provisioning: backfill cannot enter the hot path. A reconnecting plant regains live visibility within seconds, whatever the size of its backlog.
- **Positive:** Genealogy and alerts are never stuck behind bulk telemetry, which protects driver 3 and driver 2 during the moments that matter most.
- **Negative / accepted trade-off:** Downstream consumers must handle late, out-of-order data correctly (event-time windows, restatement). This is a design obligation for every cold-path consumer on every platform track in Steps 6–8, not an optional refinement.
- **Negative / accepted trade-off:** The live-horizon and backfill-cap settings are operational tuning knobs per plant. Wrong values either hurt catch-up time or crowd the link, so they are managed centrally through Fleet Management.
