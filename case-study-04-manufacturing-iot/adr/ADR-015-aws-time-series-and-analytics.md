# ADR-015: AWS Time-Series and Analytical Stores

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 4 pipeline

## Context

C6 needs 90 days of raw telemetry at 60K+ values/sec, with late data placed by source timestamp. C7 needs 5 years of 1-minute data plus training sets. C9/C10 need one OEE definition, restatement when late data arrives, and aggregates-only flow from the EU. The data team is four people.

Two facts from AWS narrow the options:

- **Amazon Timestream for LiveAnalytics closed to new customers on 20 June 2025.** Existing customers are unaffected, and AWS directs new customers to **Timestream for InfluxDB**. Kestrel has never used Timestream, so it is a new customer.
- **AWS IoT SiteWise** stores asset-modeled time series (with hot and cold tiers and computed metrics), and it is the native landing point for SiteWise Edge's real-time destination.

## Decision

- **C6: Amazon Timestream for InfluxDB (Multi-AZ), one instance per region**, with 90-day retention. The Flink normalizer writes both live and backfill data using source timestamps, so late data lands in the correct position. The instance class is sized in Step 12. If one instance cannot hold 90 days at US volume, the data is sharded by plant group rather than the retention cut.
- **C7: Amazon S3 Tables (Apache Iceberg), queried with Amazon Athena.** It holds 1-minute downsampled data for 5 years, machine-state history, OEE facts, and curated training sets. The downsampling job is Flink (streaming) or Glue (scheduled).
- **C9/C10:** OEE is calculated once, as Athena/Glue jobs over S3 Tables, with restatement triggered by backfill-affected shift partitions. **Amazon QuickSight** serves business reporting and **Amazon Managed Grafana** serves plant engineers (reading InfluxDB and Athena). EU aggregate tables are **replicated** (copied) to the US global bucket. There is no cross-region querying of raw EU data.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Timestream for LiveAnalytics.** Not available to Kestrel as a new customer since 20 June 2025. It is recorded here because it was AWS's flagship IoT time-series service. Its closure is the AWS counterpart of Azure Time Series Insights' retirement, and both feed the ecosystem-churn risk in `requirements.md`.
2. **AWS IoT SiteWise as C6 and the asset model of record.** Considered seriously. It is industrial-native (asset hierarchies, computed metrics that can express OEE, and a direct edge integration). Rejected as the *enterprise* store for three reasons:
   - The enterprise asset model already lives in the UNS topic hierarchy ([ADR-002](ADR-002-plant-data-integration-pattern.md)). Making SiteWise's model authoritative would create a second, AWS-specific model of record.
   - Ingestion and storage are priced per data point, which at about 5 billion values a day is a cost-risk profile Step 12 would have to justify.
   - Late-data restatement and ML training still need an open analytical copy, so SiteWise would be an *addition*, not a replacement.

   It stays a candidate for plant-level dashboards on a subset of assets.
3. **S3 + Athena only (no hot time-series store).** Rejected. Engineers' interactive 90-day queries per asset need second-scale latency, which Athena over Iceberg does not reliably give at this cardinality.

## Consequences

- **Positive:** C7 is in an open table format (Iceberg on S3). Training data and history are portable, which offsets the proprietary stream layer ([ADR-014](ADR-014-aws-ingestion-and-hot-path.md)).
- **Positive:** InfluxDB is a widely known open-source time-series engine, so engineers' skills and queries carry over.
- **Negative / accepted trade-off:** There are four products here (InfluxDB, S3 Tables/Athena, QuickSight, and Grafana), against Azure's single Fabric platform ([ADR-009](ADR-009-azure-time-series-analytics-and-hot-path.md)). That is more to operate and secure for a four-person team, and it is scored under operational fit.
- **Negative / accepted trade-off:** Timestream for InfluxDB scales by instance (and replicas), not elastically. The 150K values/sec growth target (NFR-3) may need sharding, which Step 12 must cost.
