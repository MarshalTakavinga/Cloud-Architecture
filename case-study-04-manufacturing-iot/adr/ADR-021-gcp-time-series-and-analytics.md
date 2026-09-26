# ADR-021: GCP Time-Series and Analytics — Manufacturing Data Engine → Bigtable + BigQuery

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 4 pipeline

## Context

C3, C6, C7, and C9/C10 carry the same requirements as on the other tracks. Google's **Manufacturing Data Engine (MDE)** is a packaged solution deployed into the customer's project. It ingests through a Pub/Sub `input-messages` topic, maps messages (Whistle transformations), and contextualizes them against standards including the "ISA-95 hierarchy … OPC-UA … Asset Administration Shell". It writes to **BigQuery, Bigtable, and Cloud Storage**. According to Google there are "no extra costs for using MDE"; the customer pays for cloud consumption only.

## Decision

- **C3: MDE**, deployed per region. A small forwarding subscription feeds both `telemetry-live` and `telemetry-backfill` into MDE's input topic, with a lane attribute on each message. MDE's pipeline normalizes and deduplicates on `(site, source, sequence)`, and it maps each message to the ISA-95 asset model already defined by the UNS topics (so no second model of record is created).
- **C6: Bigtable**, with row keys of `site#asset#signal#reversed-timestamp` and a 90-day garbage-collection policy. Writes are by source timestamp, so late data lands in the correct position.
- **C7: BigQuery**, with 5 years of 1-minute data, machine-state history, and training sets, partitioned by day and clustered by site and asset.
- **C9/C10: OEE** as BigQuery scheduled and incremental queries, with restatement of backfill-affected partitions, and **Looker** for dashboards. EU aggregate tables are copied into the US global dataset. Raw EU datasets stay in europe-west3 inside the EU VPC Service Controls perimeter.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Build the pipeline in Dataflow without MDE.** Rejected. It means rebuilding the mapping, contextualization, and multi-sink writing that Google already packages at no license cost. MDE is the least-build cloud pipeline of the three tracks.
2. **BigQuery only (no Bigtable).** Considered. BigQuery can hold 90 days, but engineers' high-frequency, per-asset interactive reads are a better match for Bigtable's single-row-range latency, while BigQuery suits scans and aggregates. The split mirrors hot and cold access patterns.
3. **Rely on Litmus's own cloud products for analytics.** Rejected. It would add a fourth vendor to the data path, and the analytical store would sit outside Kestrel's governed GCP perimeter.

## Consequences

- **Positive:** BigQuery is the strongest analytical engine for a four-person data team among the three tracks (serverless, SQL, native ML via BigQuery ML), and Vertex AI trains directly from it.
- **Positive:** The only manufacturing-specific component on the cloud side, MDE, is licence-free and deployed into Kestrel's own project. Kestrel keeps the code, and the durable data is in open or standard stores.
- **Negative / accepted trade-off:** MDE is a packaged solution deployed as scripts and code into the project, **not a managed service**. Kestrel owns running and upgrading it, which is a quieter operational commitment than the phrase "Google product" suggests.
- **Negative / accepted trade-off:** Bigtable nodes are provisioned capacity, so a baseline cost applies (sized in Step 12).
