# ADR-014: AWS Ingestion, Stream Processing, and Hot Path

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 4 pipeline

## Context

C1–C5 need four things:
- durable, partitioned, replayable streams (live, alerts, backfill, genealogy) per region
- normalization and deduplication with event-time semantics
- a hot path on **live data only** that delivers SAP PM notifications within 5 minutes (NFR-5)
- throughput of 60K values/sec, growing to 150K, with 300K/sec backfill bursts (NFR-3/NFR-4)

Stream manager exports natively to **Kinesis Data Streams**, S3, and IoT SiteWise.

## Decision

- **C1/C2: Amazon Kinesis Data Streams in on-demand capacity mode.** There are four streams per region (us-east-2 and eu-central-1), partitioned by `site + asset` (and `site + part number` for genealogy), with 7-day retention and interface VPC endpoints.
  - On-demand absorbs backfill bursts without shard pre-planning. Provisioned mode is re-evaluated in Step 12 once steady-state volume is measured.
- **C3/C4: Amazon Managed Service for Apache Flink, running two applications.**
  - **Normalizer:** reads all three telemetry streams, validates schemas, deduplicates on `(site, source, sequence)` with keyed state, and writes to C6 and C7 using event time.
  - **Hot path:** reads **`telemetry-live` and `alerts` only**, which enforces ADR-005 by its source binding. It computes windowed features and calls an **Amazon SageMaker AI** real-time endpoint for RUL. Recommendations go to **SQS FIFO**, with a deterministic recommendation ID used as the deduplication ID.
- **C5: AWS Lambda** consumes SQS and creates SAP PM notifications through SAP's OData service over the Columbus VPN. An idempotency record per recommendation ID is kept in DynamoDB.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Amazon MSK (managed Kafka).** It is fully capable, and it is Kafka-native, which helps portability. Rejected because stream manager does **not** export to Kafka natively, so a custom producer would be needed at every plant. There would also be brokers to size and patch for a team without streaming operations experience. Kinesis is the lower-friction path on this platform.
2. **AWS IoT Core rules → Kinesis, with plants publishing MQTT to IoT Core.** Rejected as the data path, because it would bypass stream manager's priorities and persistence. IoT Core is still used for device identity and Greengrass control traffic ([ADR-017](ADR-017-aws-network-identity-and-deployment.md)).
3. **Lambda for the hot path.** Rejected. It would mean hand-building windowing, late-event handling, and state that Flink provides.
4. **SiteWise as the landing zone for real-time data (the V3 gateway's real-time destination).** Considered, and discussed in [ADR-015](ADR-015-aws-time-series-and-analytics.md). Rejected as the primary path because the gateway allows **one** real-time destination, and routing through SiteWise would put the hot path behind a store rather than a stream.

## Consequences

- **Positive:** The edge-to-cloud path is native end to end (stream manager → Kinesis), including lane priority, with no custom producers.
- **Positive:** Flink gives the strongest event-time and late-data semantics of the three tracks, which directly serves ADR-005's restatement obligation.
- **Negative / accepted trade-off:** Flink is powerful but demanding. Checkpointing, state sizing, and application upgrades need streaming engineering skills that Kestrel does not have today. This is scored under operational/skills fit.
- **Negative / accepted trade-off:** Kinesis is AWS-proprietary (not Kafka-compatible), so portability of the stream layer is lower than with Event Hubs' Kafka endpoint on Azure.
