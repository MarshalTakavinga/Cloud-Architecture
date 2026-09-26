# ADR-019: GCP Implementation of the Four-Lane Outbox and Genealogy Journal

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 4 pipeline

## Context

[ADR-005](ADR-005-store-and-forward-and-backfill-lanes.md) and [ADR-004](ADR-004-genealogy-exactly-once-record-path.md) set the requirements, as on the other tracks. On GCP there is **no native edge service with priority-aware buffering**:
- MCe has store-and-forward, but no documented priorities, live horizon, or rate cap.
- GDC is a Kubernetes platform, not a messaging service.
- Pub/Sub is cloud-side only.

Azure provided lanes 2–3 natively ([ADR-007](ADR-007-azure-store-and-forward-implementation.md)), and AWS provided all four lanes' mechanics ([ADR-013](ADR-013-aws-store-and-forward-implementation.md)).

## Decision

Kestrel builds a single **Outbox Service** (a StatefulSet on the GDC cluster, with replicated persistent volumes):

- **Lanes:** four disk-backed queues, drained in **strict priority** (genealogy > alerts > live > backfill).
- **Live horizon:** lane 3 drops entries older than 5 minutes. They are not lost, because lane 4 recovers them from P8.
- **Lane 4:** **gap-based backfill** from P8 (TimescaleDB) against per-source cloud watermarks, under a per-plant bandwidth cap.
- **Publishing:** to Pub/Sub, with **ordering keys** per `site + asset` (or per `site + part number` for genealogy). A queue entry is released only after Pub/Sub acknowledges the publish.
- **Identity:** fleet Workload Identity, with no stored keys.

**Genealogy:** the P6 journal is PostgreSQL (CloudNativePG) with a synchronous standby, the same as on Azure. The Outbox Service reads lane 1 directly from the journal, so the journal is the queue.

**MCe's own store-and-forward** is left enabled as a safety net for its local broker connection only. MCe does not publish to the cloud.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Let MCe publish telemetry directly to Pub/Sub (its documented integration) and build only lanes 1, 2, and 4.** Considered. It would use a native path, but it gives no live-horizon control. After an outage MCe drains its own buffer in its own order, which is ADR-005's FIFO problem, and it would put a service-account key in every plant. Rejected.
2. **Deploy an open-source stream processor at the edge (for example, a Kafka or Redpanda cluster per plant) as the outbox.** Rejected. It would be a heavy fourth edge product to operate in 12 plants for what is a small, well-defined queueing job.
3. **Push backfill to Cloud Storage as files.** Rejected for the same reasons as on Azure and AWS: no per-source gap control, and it would land outside the backfill stream.

## Consequences

- **Positive:** The lane semantics are exactly as ADR-005 specifies, including strict priority, which Azure's parallel queues only approximated.
- **Positive:** One Kestrel component owns the whole plant-to-cloud contract, which is easy to test and reason about.
- **Negative / accepted trade-off:** This is the **most Kestrel-built edge code of the three tracks**. The outbox is on the critical data path for all 12 plants, and it is software Kestrel must write, test, and support for the life of the platform. It is scored as build effort and risk in Step 9.
- **Negative / accepted trade-off:** Pub/Sub ordering keys constrain per-key publish throughput. Keys are therefore per asset, never per plant, so that one busy plant's backfill does not serialize behind a single key.
