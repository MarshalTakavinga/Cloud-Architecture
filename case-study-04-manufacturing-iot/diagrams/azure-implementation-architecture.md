# Diagram: Azure Implementation Architecture (Step 6)

Source of truth for the Step 6 diagram referenced in [`docs/azure-implementation.md`](../docs/azure-implementation.md) and [ADR-006](../adr/ADR-006-azure-edge-platform.md) to [ADR-011](../adr/ADR-011-azure-network-identity-and-deployment.md). Mermaid renders natively on GitHub. The same shape is deployed in two regions: East US 2 for the 10 US/Mexico plants, and Germany West Central for Plants 11–12.

```mermaid
flowchart LR
    subgraph PLANT["Plant (×10 US/MX · ×2 DE)"]
        direction TB
        L2["Level 2 OPC UA servers\n(+ protocol gateways)"]
        STN["Station / MES"]
        subgraph K3S["Level 3 — 3-node Arc-enabled K3s cluster"]
            direction TB
            subgraph AIO["Azure IoT Operations"]
                OPC["Connector for OPC UA\n(Device Registry assets)"]
                MQTT[["MQTT broker\n(persistence on)"]]
                DF2["Data flow: alerts\n(disk persistence)"]
                DF3["Data flow: live\n(5-min expiry)"]
                DF8["Data flow: → local TSDB"]
            end
            subgraph KBUILT["Kestrel-built containers"]
                FEAT["P3 Feature extractor"]
                ANOM["P4 Anomaly detector\n(ONNX Runtime)"]
                REC["P5 Genealogy recorder"]
                FWD["Lane 1 journal forwarder"]
                BF["Lane 4 backfill uploader\n(gap-based, rate-capped)"]
                ACT["Model activation controller"]
            end
            JRN[("P6 Journal\nPostgreSQL sync standby")]
            TSDB[("P8 TimescaleDB\n30 days")]
            FLUX["Arc GitOps (Flux)"]
        end
        subgraph DMZ["Level 3.5 — DMZ"]
            ENVOY["Envoy explicit proxy\n(allowlist · Arc gateway)"]
            CREG["ACR connected registry\n(ReadOnly)"]
        end
        L2 -- "OPC UA read" --> OPC
        OPC --> MQTT
        FEAT --> MQTT
        MQTT --> ANOM
        MQTT --> DF2
        MQTT --> DF3
        MQTT --> DF8
        DF8 --> TSDB
        STN <--> REC
        REC --> JRN
        JRN --> FWD
        TSDB --> BF
        FWD --> ENVOY
        DF2 --> ENVOY
        DF3 --> ENVOY
        BF --> ENVOY
        CREG -. "pull images" .-> FLUX
        FLUX -. "deploy" .-> ACT
        ACT -. "shadow → approve → active" .-> ANOM
    end

    COL["Columbus DC\n(MPLS hub · SAP ECC)"]

    subgraph AZ["Azure region (East US 2 · Germany West Central for DE)"]
        direction TB
        subgraph EH["Event Hubs Premium (private endpoint)"]
            HG[["genealogy"]]
            HA[["alerts"]]
            HL[["telemetry-live"]]
            HB[["telemetry-backfill"]]
        end
        ASA["Stream Analytics\n(live + alerts only)"]
        AML["Azure ML\n(online endpoint · training · registry)"]
        SB[["Service Bus"]]
        LA["Logic Apps Standard\n(SAP connector)"]
        subgraph FAB["Microsoft Fabric"]
            ES["Eventstream"]
            EVH[("Eventhouse\n90 days")]
            LH[("Lakehouse\n5 years")]
            PBI["OEE · Power BI"]
        end
        SQL[("Azure SQL Hyperscale\nappend-only ledger tables")]
        BLOB[("Immutable Blob\ndigests + 15-yr archive")]
        ACR["Azure Container Registry\n(signed images)"]
        GIT["Git repo\n(per-plant branches)"]
        ARC["Azure Arc · Device Registry\n· Policy · Monitor"]
    end

    ENVOY -- "outbound only" --> COL
    COL -- "site-to-site VPN\n(DE plants: direct VPN to EU)" --> EH
    HG --> SQL
    SQL --> BLOB
    HA --> ASA
    HL --> ASA
    HA --> ES
    HL --> ES
    HB --> ES
    ES --> EVH
    EVH --> LH
    LH --> PBI
    LH --> AML
    ASA <--> AML
    ASA --> SB
    SB --> LA
    LA -- "PM notification" --> COL
    ACR -. "sync" .-> CREG
    GIT -. "pulled by Flux" .-> FLUX
    ARC -. "manages" .-> K3S
```

## How to read it

- **The Azure IoT Operations box** is what Microsoft provides at the edge. **The Kestrel-built box** is what Kestrel writes and operates. Their relative size is a Step 9 comparison point.
- **Four arrows leave the cluster, one per outbox lane,** and all go through the DMZ Envoy proxy. The backfill uploader reads from the local TimescaleDB, not from the broker ([ADR-007](../adr/ADR-007-azure-store-and-forward-implementation.md)).
- **`telemetry-backfill` feeds only Fabric, never Stream Analytics.** That is ADR-005 enforced by wiring.
- **The dotted lines are all pulls:** the connected registry syncs from ACR, Flux pulls from Git and the registry, and the activation controller gates models. Nothing in Azure initiates a connection into the plant ([ADR-011](../adr/ADR-011-azure-network-identity-and-deployment.md)).
- **P4 and P5/P6 have no arrow to Azure at runtime,** which is why the IoT Operations 72-hour offline ceiling does not reach alerting or genealogy ([ADR-006](../adr/ADR-006-azure-edge-platform.md)).
