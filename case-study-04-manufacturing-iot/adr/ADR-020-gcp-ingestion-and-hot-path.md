# ADR-020: GCP Ingestion and Hot Path — Pub/Sub + Dataflow + Vertex AI

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 4 pipeline

## Context

C1–C5 need: four streams per region, pinned to region (NFR-10); 7-day replay; live-only hot path with RUL scoring and SAP PM notifications within 5 minutes (NFR-5); and throughput to 150K values/sec with 300K/sec bursts. Pub/Sub supports message storage policies (allowed persistence regions), ordering keys, seek/replay, and exactly-once delivery for pull subscriptions. **Pub/Sub Lite was turned down on 18 March 2026.** Google Cloud Managed Service for Apache Kafka is available.

## Decision

- **C1/C2: Pub/Sub**, with four topics per region (us-east5, europe-west3). A message storage policy on each topic limits persistence to its region. Retention is 7 days, with seek for replay. Access is through Private Service Connect only.
- **C4: a Dataflow (Apache Beam) streaming job** subscribed to **`telemetry-live` and `alerts` only**, so ADR-005 is enforced by subscription. It uses event-time windows per asset, calls **Vertex AI** online prediction for RUL, and emits `MaintenanceRecommendation` with deterministic IDs to a `maintenance-recommendations` topic.
- **C5: a Cloud Run service** on a pull subscription with **exactly-once delivery** enabled. It creates SAP PM notifications via OData over the Columbus HA VPN, with the recommendation ID recorded in Firestore for idempotency.
- **C3** (normalization and deduplication) is performed by MDE's Dataflow pipeline ([ADR-021](ADR-021-gcp-time-series-and-analytics.md)).

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Managed Service for Apache Kafka.** Kafka-compatible, which helps portability. Rejected because MDE is built around Pub/Sub, and nothing at the edge needs Kafka, since the outbox is Kestrel-built either way. Choosing Kafka would mean giving up the packaged MDE pipeline or bridging to it.
2. **Pub/Sub Lite.** Turned down on 18 March 2026. It is recorded as further evidence for the churn risk.
3. **Cloud Run Functions for the hot path.** Rejected. It would mean hand-built windowing and late-data handling, as on the other tracks.

## Consequences

- **Positive:** Pub/Sub is serverless (no partitions or processing units to size), with region pinning built into the topic. This is the least capacity planning of the three tracks.
- **Positive:** Dataflow (Beam) matches Flink's event-time strength, and the Beam model is portable across runners.
- **Negative / accepted trade-off:** Pub/Sub is proprietary and not Kafka-compatible, so it is less portable than Azure's Event Hubs Kafka endpoint.
- **Negative / accepted trade-off:** Dataflow streaming jobs run continuously, so there is a steady baseline cost even when volume is low. Step 12 sizes this cost.
