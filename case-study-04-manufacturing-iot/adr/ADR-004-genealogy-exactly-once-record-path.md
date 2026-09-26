# ADR-004: Genealogy Exactly-Once Record Path

**Status:** Approved
**Date:** Step 5 of the Case Study 4 pipeline

## Context

Driver 3 and NFR-6 require serial-level genealogy with **zero loss and no duplicates**: a missing or duplicated serial record is a quality-system nonconformance, not just a data bug. NFR-8 requires 15-year immutable retention, and NFR-7 requires per-serial queries in ≤ 5 seconds.

Three constraints shape the design:

- **Plant autonomy.** Genealogy must keep being captured during WAN outages (NFR-1), so the cloud cannot be in the write path.
- **No reliable single hop.** The path from station to cloud crosses several hops (station → recorder → UNS broker → outbox → DMZ bridge → ingestion → stream → store), and each of them delivers at-least-once at best.
- **Uneven MES coverage.** Only four of the 12 plants have an MES, so the MES cannot be the system of record for genealogy everywhere.

## Decision

1. **Identity.** Every record is keyed by **`(part number, serial, record version)`**. The laser-marked serial is unique within a part number. Version 1 is the as-built record. Rework or re-inspection appends version 2, and so on, which reference the prior version. **Records are never updated in place.**
2. **Durable at the edge before confirmation.** The Genealogy Recorder appends the record to a local, append-only **journal**, where each entry carries the hash of the previous entry (a hash chain). It waits for synchronous replication to the second edge node, and only then returns `SerialRecorded` to the station or MES. If the write cannot complete, the station receives `SerialHeld` and the part goes to a hold-for-genealogy bin. **The line keeps running, and an untraced part cannot ship.**
3. **Exactly-once outcome on at-least-once transport.** From the journal onward, every hop may redeliver. The Genealogy Store enforces **uniqueness on the key**:
   - A redelivered record with the same key and the same content hash is a no-op.
   - A record with the same key but a **different** content hash is not overwritten. It is raised as a quality-system exception, because it indicates either a serial-marking fault or tampering.
4. **Verification, not trust.** Every night, each plant's journal hash-chain head and record count are compared with the cloud store's view of that plant. A mismatch is an exception for investigation, never an automatic correction.
5. **Immutability.** The cloud store is write-once for the 15-year retention period (NFR-8). The local journal keeps at least 90 days, so the plant can answer genealogy lookups on its own during an outage.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Rely on MQTT QoS 2 ("exactly once").** Rejected as the mechanism. QoS 2 guarantees exactly-once only for **one client-to-broker hop**. It says nothing about the bridge, the ingestion endpoint, the stream, or the store, and it offers no durability if the broker node is lost before a subscriber reads. Genealogy still travels over the UNS for local visibility, but correctness does not depend on it.
2. **Write genealogy directly to the cloud store.** Rejected. It fails NFR-1: a WAN outage would either stop serial confirmation, and so stop the line, or let parts ship untraced.
3. **Make the MES the genealogy system of record.** Rejected. Only four plants have an MES, and those four are two different products. Where an MES exists it *calls* the Recorder instead of the station doing so, so it stays the system of record for work orders but not for genealogy.
4. **Let the cloud assign record IDs.** Rejected. Identity would depend on connectivity, and edge and cloud could disagree after an outage. The physical serial already is the identity.

## Consequences

- **Positive:** Deduplication and conflict detection live in exactly one place (the Genealogy Store's key constraint). Integrity is provable end to end by the hash chain, which is the kind of evidence an OEM supplier-quality audit asks for.
- **Positive:** A genealogy fault never stops production. It only diverts parts to a hold bin, which is protecting driver 5 and driver 3 at the same time.
- **Negative / accepted trade-off:** Serial confirmation now depends on a local synchronous write replicated across two edge nodes. If both nodes are down, every serialized part goes to hold. This is safe but costly, so edge-node availability for the Recorder is a first-class monitoring target and appears in the Step 12 risk register.
- **Negative / accepted trade-off:** Stations at non-MES plants need a small integration to call the Recorder. At some, a serial scanner at the station is enough. At others, the PLC signals cycle-complete via the connector. This is plant-engineering work that is sized per plant in Step 11.
