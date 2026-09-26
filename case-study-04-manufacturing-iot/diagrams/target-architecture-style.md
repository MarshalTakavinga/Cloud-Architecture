# Diagram: Target Architecture Style (Step 4)

Source of truth for the Step 4 target-style diagram referenced in [`docs/architecture-options-and-styles.md`](../docs/architecture-options-and-styles.md) and [ADR-001](../adr/ADR-001-edge-cloud-responsibility-split.md) to [ADR-003](../adr/ADR-003-ot-segmentation-reference-architecture.md). Mermaid renders natively on GitHub.

```mermaid
flowchart LR
    subgraph Plant["Each plant (×12) — autonomous spoke"]
        direction TB
        subgraph L012["Levels 0–2 (retained, read-only)"]
            PLC["PLCs / safety / drives"]
            SCADA["SCADA / HMI\nOPC UA servers"]
            PLC --- SCADA
        end
        subgraph L3["Level 3 — site operations zone"]
            CONN["Edge connectors\nOPC UA → Sparkplug B\n(asset-model mapping)"]
            UNS[["Plant UNS\nMQTT broker"]]
            EDGE["Edge compute\nanomaly detection · local alerts\n72h+ store-and-forward buffer"]
            GEN["Genealogy capture\n(durable local write)"]
            HIST["Existing historian / MES\n(retained, subscribe)"]
        end
        subgraph DMZ["Level 3.5 — industrial DMZ"]
            BRIDGE["Cloud bridge\n(outbound-only)"]
            SRA["Secure remote access\n(MFA, brokered)"]
        end
        SCADA -- "OPC UA (read)" --> CONN
        CONN --> UNS
        UNS <--> EDGE
        UNS <--> HIST
        GEN --> UNS
        UNS -- "single conduit" --> BRIDGE
    end

    subgraph Cloud["Cloud hub (US region + EU region for DE plants)"]
        direction TB
        ING[["Ingestion / event stream"]]
        HOT["Hot path\nstream processing · predictive insights"]
        COLD["Cold path\ntime-series + analytical store\nOEE · training data"]
        GSTORE["Genealogy store\nimmutable · 15 years"]
        ML["Model training + registry"]
        ING --> HOT
        ING --> COLD
        ING --> GSTORE
        COLD --> ML
    end

    SAP["SAP ECC → S/4HANA\n(PM notifications / work orders)"]
    KPI["Global KPI / OEE layer\n(aggregated, non-personal)"]

    BRIDGE -- "outbound TLS" --> ING
    HOT --> SAP
    COLD --> KPI
    ML -. "versioned model deploy\n(via DMZ, pulled by edge)" .-> EDGE
```

## How to read this diagram

- **Levels 0–2 are untouched.** The only arrow out of them is a *read* over OPC UA into the edge connectors. Nothing points back in.
- **The plant UNS broker is the hub inside each plant.** The historian, MES, edge analytics, and cloud bridge all subscribe to it instead of each connecting to the machines ([ADR-002](../adr/ADR-002-plant-data-integration-pattern.md)).
- **The DMZ is the only place the plant meets the outside.** The cloud bridge makes outbound connections only. Model deployments are *pulled* by the edge through the DMZ, not pushed in from the cloud ([ADR-003](../adr/ADR-003-ot-segmentation-reference-architecture.md)).
- **Everything in the plant box keeps working if the "outbound TLS" arrow is cut.** That is NFR-1, and it is why the edge compute holds the store-and-forward buffer ([ADR-001](../adr/ADR-001-edge-cloud-responsibility-split.md)).
- **The cloud box is platform-neutral on purpose.** Steps 6–8 swap in each platform's services for ingestion, stream processing, storage, and ML without changing this shape.
