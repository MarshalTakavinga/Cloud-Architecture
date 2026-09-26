# ADR-009: Azure Time-Series, Analytics, and Hot Path

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 4 pipeline

## Context

Step 5 separates four cloud workloads:
- **C4 hot path:** live-only stream processing and remaining-useful-life (RUL) scoring, with SAP PM notification within 5 minutes (NFR-5)
- **C6 hot time series:** 90 days, accepting late data by source timestamp
- **C7 analytical store:** 5 years of 1-minute data, plus ML training sets
- **C9/C10 OEE and KPIs:** one definition, restated when late data arrives, with only aggregates crossing from EU to global

Kestrel's data team is four data scientists, and there is no data-platform engineering team, so the number of separate products to operate matters as much as capability. Azure's own history adds context: Azure Time Series Insights, a purpose-built IoT time-series service, was retired in 2024. That is the same pattern of ecosystem churn named as a risk in `requirements.md`.

## Decision

1. **C6 and C3: Microsoft Fabric Real-Time Intelligence.**
   - An **Eventstream** reads `telemetry-live`, `alerts`, and `telemetry-backfill` and validates schemas.
   - Data lands in an **Eventhouse** (KQL database), which is built for high-rate time series. It uses ingestion-time deduplication on `(site, source, sequence)` and event-time (source-timestamp) queries, so late backfill lands in the correct time position without special handling.
   - Hot retention is 90 days.
2. **C7: a Fabric Lakehouse (OneLake, Delta).**
   - It holds 1-minute downsampled telemetry for 5 years, machine-state history, OEE facts, and curated training sets.
   - Downsampling runs as scheduled KQL-to-Delta materialization, so the analytical store and the time-series store share one copy of the platform.
3. **C4: Azure Stream Analytics.**
   - It consumes **`telemetry-live` and `alerts` only**, which enforces ADR-005 through its input binding.
   - It runs windowed aggregations per asset and calls an **Azure Machine Learning online endpoint** for RUL scoring on critical assets.
   - Output goes to an **Azure Service Bus** queue as `MaintenanceRecommendation`, each with a deterministic recommendation ID.
4. **C5: Logic Apps Standard with the SAP connector.**
   - It consumes the queue and creates SAP PM notifications, and it is idempotent on recommendation ID. SAP ECC is reached over the Columbus site-to-site VPN ([ADR-011](ADR-011-azure-network-identity-and-deployment.md)).
   - Moving to S/4HANA changes this workflow only.
5. **C9 and C10: OEE in Fabric (KQL and SQL), with Power BI.**
   - The OEE calculation is defined once. Restatement runs whenever backfill touches a shift that has already been reported.
   - The EU Fabric capacity (Germany West Central) publishes **aggregated, non-personal** OEE tables. A pipeline *copies* them into the US global workspace. There are no cross-region shortcuts to raw EU data.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Standalone Azure Data Explorer for C6, with ADLS plus Databricks or Synapse for C7.** Technically equivalent for time series (Eventhouse uses the same KQL engine). Rejected because it means three to four separately provisioned and secured products for a four-person data team. Fabric puts time series, lakehouse, pipelines, and BI in one capacity-billed platform. ADX would be the choice if Kestrel already had an ADX estate. It does not.
2. **Fabric-only hot path, using KQL update policies and Fabric Activator instead of Stream Analytics.** Considered. It would remove one more product. Rejected *for the hot path specifically* because C4's contract is "live only, never backfill", and a Stream Analytics job bound to the live and alerts hubs enforces that structurally. A KQL-based trigger would query a table that *also* receives backfill and would have to filter it correctly every time. It can be revisited once backfill lands in separate tables by design.
3. **Azure Functions for C4.** Rejected. It would mean hand-writing windowing, late-arrival handling, and state management that Stream Analytics provides.

## Consequences

- **Positive:** The data team works in one platform (Fabric) for exploration, training data, OEE, and dashboards, with time series and lakehouse sharing one governance model.
- **Positive:** The hot path's inputs make it structurally impossible to score stale backfill as if it were current.
- **Negative / accepted trade-off:** Fabric capacity is billed per capacity, separately in each region (US and EU). An undersized EU capacity would be shared by relatively little data, but its minimum cost still applies. This is sized in Step 12.
- **Negative / accepted trade-off:** Kestrel is taking a dependency on Microsoft's newest analytics platform on a track whose history includes a retired IoT time-series service. The mitigation is that the durable assets are open formats (Delta tables in OneLake, a Kafka-compatible stream), so any product change would be a migration, not a loss of data.
