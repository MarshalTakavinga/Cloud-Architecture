# ADR-013: AWS Implementation of the Four-Lane Outbox and Genealogy Journal

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 4 pipeline

## Context

[ADR-005](ADR-005-store-and-forward-and-backfill-lanes.md) requires four lanes with genealogy and alerts first, a seconds-to-live reconnect, rate-capped backfill, and a separate cloud backfill stream. [ADR-004](ADR-004-genealogy-exactly-once-record-path.md) requires a durable, synchronously replicated, hash-chained journal before `SerialRecorded` is returned.

**Greengrass stream manager** provides:
- persistent streams (`File` persistence, optional `flush_on_write`)
- per-message `time_to_live_millis`
- `strategy_on_full`: `RejectNewData` or `OverwriteOldestData`
- per-export **priority** ("lower values are higher priority")
- `start_sequence_number` and a `disabled` flag on each export
- an exporter-wide maximum bandwidth
- native export to Kinesis Data Streams, S3, and IoT SiteWise

## Decision

| Lane | Stream manager stream | Settings | Export |
|---|---|---|---|
| **1 — Genealogy** | `genealogy` | `File`, `flush_on_write`, `RejectNewData`, large size cap | Kinesis `genealogy`, **priority 1** |
| **2 — Alerts** | `alerts` | `File`, `RejectNewData` | Kinesis `alerts`, **priority 2** |
| **3 — Live** | `live` | `File`, **TTL 5 min**, `OverwriteOldestData` | Kinesis `telemetry-live`, **priority 3** |
| **4 — Backfill** | `history` | `File`, size cap for about 7 days, `OverwriteOldestData` | Kinesis `telemetry-backfill`, **priority 10**, **export disabled in normal running** |

- **Publishing:** a Kestrel-built component subscribes to the UNS and appends each message to both `live` and `history`. Genealogy is written directly to `genealogy` by the Recorder (P5), and `SerialRecorded` is returned only after the append returns with `flush_on_write`.
- **Synchronous replication (ADR-004):** the stream manager directory sits on the **DRBD protocol C** volume ([ADR-012](ADR-012-aws-edge-platform.md)), so a flushed write is on both nodes before it is acknowledged. A SQLite index on the same volume serves local per-serial lookups during outages.
- **Backfill controller (Kestrel-built, control logic only):** after reconnecting, it compares the `history` stream with per-source cloud watermarks. It then enables the `history` export from the first missing sequence number and disables it again when caught up. Stream manager does the data movement.
- **Bandwidth:** the exporter-wide maximum bandwidth is set per plant (for example, 60% of the link). Priority ordering means lane 4 is what yields first under the cap.
- **P8 (30-day local trending):** TimescaleDB as a Docker component. It is *not* in the lane path, unlike on Azure.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **One stream with no TTL.** Rejected, because it is ADR-005's single FIFO.
2. **Export `history` continuously.** Rejected. It would double WAN traffic and cloud ingestion every day to cover a case that occurs a few times a year.
3. **The SiteWise Edge V3 "buffered destination" (S3) for backfill.** Considered. It is native and cheap, but it lands data as S3 files outside the backfill stream the cold path consumes, and it gives no per-source gap control. It remains an option for bulk raw-waveform snapshot uploads.
4. **PostgreSQL with a synchronous standby for the genealogy journal (the Azure approach).** Rejected *on this track*. DRBD already replicates synchronously, so a second replication mechanism for one table would add a component without adding a guarantee.

## Consequences

- **Positive:** Lane priority, TTL, persistence, bandwidth capping, and export to the cloud stream are all **native**. Kestrel's code on the lane path is one small controller, compared with two data-path services on Azure ([ADR-007](ADR-007-azure-store-and-forward-implementation.md)).
- **Positive:** The genealogy journal *is* the lane 1 stream, so there is one copy with nothing to reconcile locally.
- **Negative / accepted trade-off:** The durability of genealogy now depends on DRBD being healthy. A degraded DRBD pair (one node down) must switch the Recorder to "single-node durable" and alert immediately, or else fail safe to `SerialHeld`. Kestrel chooses **alert and continue on one node for up to one shift**, then `SerialHeld`. This is a configurable policy and is logged in the Step 12 risk register.
- **Negative / accepted trade-off:** `OverwriteOldestData` on `history` means an outage longer than about 7 days would lose the oldest backfill. That is far beyond NFR-1's 72 hours, and P8 still holds 30 days locally for manual recovery.
