# ADR-007: Azure Implementation of the Four-Lane Outbox and Genealogy Journal

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 4 pipeline

## Context

[ADR-005](ADR-005-store-and-forward-and-backfill-lanes.md) requires four lanes (genealogy, alerts, live, backfill). A reconnecting plant must go live within seconds, and backfill must be rate-capped and kept out of the cloud hot path. [ADR-004](ADR-004-genealogy-exactly-once-record-path.md) requires a hash-chained journal that is synchronously replicated before a serial is confirmed.

IoT Operations data flows buffer through the MQTT broker's **subscriber queue**. During an outage the data flow does not acknowledge messages, the broker keeps them queued, and on reconnect they are delivered **oldest first**. With broker persistence and `requestDiskPersistence` enabled, the queue survives restarts. Microsoft's documentation states that buffering is bounded: it is subject to queue limits, the disk-backed buffer size, persistence configuration, and message expiry. A single data flow is therefore the FIFO that ADR-005 rejected.

## Decision

| Lane | Azure implementation |
|---|---|
| **1 — Genealogy** | P6 journal = **PostgreSQL (CloudNativePG)** with `synchronous_commit` to a standby on a second node. The Genealogy Recorder (P5) commits the row, including the previous row's hash, before returning `SerialRecorded`. A Kestrel-built **journal forwarder** reads uncommitted-to-cloud rows **in journal order** and sends them to the `genealogy` event hub. It advances its checkpoint only after Event Hubs acknowledges. The journal *is* the lane 1 queue, so there is no second copy. |
| **2 — Alerts** | A dedicated IoT Operations **data flow** from `kestrel/+/alerts/#` to the `alerts` event hub, with broker persistence and `requestDiskPersistence` enabled. It has its own subscriber queue, so it never waits behind telemetry. |
| **3 — Live** | A separate data flow for telemetry, features, and state events to `telemetry-live`, with disk persistence **and a 5-minute message expiry**. After an outage the queue holds at most the last 5 minutes, so the plant is live within seconds of reconnecting. Older messages expire from *this lane only*. They are not lost, because lane 4 recovers them. |
| **4 — Backfill** | P8 (**PostgreSQL + TimescaleDB**, 30-day retention, fed by its own data flow) is the durable record of everything. A Kestrel-built **backfill uploader** compares P8 with per-source cloud watermarks (the highest contiguous sequence the cloud holds) and uploads the missing ranges to `telemetry-backfill`. It runs only while lanes 1–3 are drained, under the per-plant bandwidth cap. |

In practice, lanes 1–3 drain **in parallel on separate queues** rather than in strict priority order. Each has its own queue, so a small genealogy or alert message never waits behind bulk telemetry, which is what ADR-005 actually protects. Lane 4 is the only one under the rate cap.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **One data flow for all telemetry, with disk persistence and no expiry.** Rejected. It is exactly ADR-005's single FIFO: after 19 hours, Ramos Arizpe's current data would sit behind about 45 minutes of backlog.
2. **Put genealogy through a data flow as well.** Rejected. The broker queue is bounded and subject to expiry settings, and the journal must *be* the durable record, not a queue in front of it. A queue-based path would also add a second copy that could diverge.
3. **Arc Edge Volumes with cloud ingest (local files that upload to Blob when connected) for backfill.** Considered. It gives native store-and-forward of files, but it does not provide per-source gap detection or a bandwidth cap, and it would land backfill in Blob rather than in the backfill stream the cold path consumes. It remains a candidate for bulk raw-waveform snapshot uploads later, but not for the backfill lane.

## Consequences

- **Positive:** The ADR-004 and ADR-005 semantics are fully met on Azure: synchronous durable genealogy, lane isolation, a seconds-to-live recovery, and gap-based, rate-capped backfill.
- **Positive:** Gap-based backfill is self-healing. It fills *any* hole the cloud is missing, whether from an outage, a dropped batch, or a lane 3 expiry, rather than relying on a queue having held everything.
- **Negative / accepted trade-off:** Two of the four lanes rely on Kestrel-built services (the journal forwarder and the backfill uploader), plus two PostgreSQL clusters per plant to operate. This is more custom edge code than a platform with priority-aware native buffering would need, and it is compared directly in Step 9.
- **Negative / accepted trade-off:** Lane 3's expiry and lane 4's cap are configuration that must be tuned per plant and delivered through GitOps ([ADR-011](ADR-011-azure-network-identity-and-deployment.md)).
