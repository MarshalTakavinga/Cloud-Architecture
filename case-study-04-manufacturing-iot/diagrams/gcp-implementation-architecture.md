# Diagram: GCP Implementation Architecture (Step 8)

Reference source (Mermaid) for the Step 8 diagram in [`docs/gcp-implementation.md`](../docs/gcp-implementation.md) and [ADR-018](../adr/ADR-018-gcp-edge-platform.md) to [ADR-023](../adr/ADR-023-gcp-network-identity-and-deployment.md). A hand-drawn version will be produced from this source. The same shape is deployed in us-east5 (Columbus, for US/MX plants) and europe-west3 (Plants 11–12).

```mermaid
flowchart LR
    subgraph PLANT["Plant (×10 US/MX · ×2 DE)"]
        direction TB
        L2["Level 2 OPC UA servers\n+ native PLC drivers"]
        STN["Station / MES"]
        subgraph GDC["Level 3 — 3-node GDC bare-metal cluster (edge profile)"]
            direction TB
            MCE["Manufacturing Connect edge\n(Litmus) ×1–2 · Sparkplug B"]
            BRK[["Clustered MQTT broker\n(commercial)"]]
            subgraph KB["Kestrel-built"]
                FEAT["P3 Feature extractor"]
                ANOM["P4 Anomaly detector (ONNX)"]
                REC["P5 Genealogy recorder"]
                OUT["Outbox service\n4 lanes · strict priority\n5-min live horizon · rate cap"]
                ACT["Activation controller"]
            end
            JRN[("P6 Journal\nPostgreSQL sync standby")]
            TSDB[("P8 TimescaleDB\n30 days")]
            CS["Config Sync"]
        end
        subgraph DMZ["Level 3.5 — DMZ"]
            PROXY["HTTPS proxy (allowlist)"]
            GITM["Git mirror"]
            HARB["Harbor registry mirror"]
        end
        L2 -- "OPC UA / native drivers (read)" --> MCE
        MCE --> BRK
        FEAT --> BRK
        BRK --> ANOM
        BRK --> OUT
        BRK --> TSDB
        STN <--> REC
        REC --> JRN
        JRN -- "lane 1" --> OUT
        TSDB -- "lane 4 gaps" --> OUT
        OUT --> PROXY
        GITM -. "pulled" .-> CS
        HARB -. "pulled" .-> CS
        CS -. "deploy" .-> ACT
        ACT -. "shadow → approve → active" .-> ANOM
    end

    COL["Columbus DC\n(MPLS hub · SAP ECC)"]

    subgraph GCP["GCP region (us-east5 Columbus · europe-west3 for DE)"]
        direction TB
        PSC["HA VPN · Private Service Connect\n· VPC Service Controls"]
        subgraph PS["Pub/Sub (message storage policy)"]
            TG[["genealogy"]]
            TA[["alerts"]]
            TL[["telemetry-live"]]
            TB[["telemetry-backfill"]]
        end
        MDE["Manufacturing Data Engine\n(Dataflow · ISA-95 context)"]
        BT[("Bigtable\n90 days")]
        BQ[("BigQuery\n5 years · OEE")]
        LK["Looker"]
        DF["Dataflow hot path\n(live + alerts only)"]
        VX["Vertex AI\n(endpoint · training · registry)"]
        CR["Cloud Run → SAP OData\n(exactly-once pull)"]
        LDR["Cloud Run loader"]
        SQL[("Cloud SQL PostgreSQL\ninsert-only + hash chain")]
        GCS[("Cloud Storage Bucket Lock\ndigests + 15-yr archive")]
        AR["Artifact Registry\n· GKE fleet · Litmus Edge Manager"]
    end

    PROXY -- "outbound only" --> COL
    COL -- "HA VPN\n(DE plants: direct to EU)" --> PSC
    PSC --> PS
    TG --> LDR
    LDR --> SQL
    SQL --> GCS
    TL --> MDE
    TB --> MDE
    TA --> MDE
    MDE --> BT
    MDE --> BQ
    BQ --> LK
    BQ --> VX
    TL --> DF
    TA --> DF
    DF <--> VX
    DF --> CR
    CR -- "PM notification" --> COL
    AR -. "sync" .-> HARB
```

## How to read it

- **Three edge vendors in one box:** Google (the GDC cluster), Litmus (MCe), and the broker vendor. Everything in "Kestrel-built" is Kestrel's code, including the whole outbox ([ADR-018](../adr/ADR-018-gcp-edge-platform.md), [ADR-019](../adr/ADR-019-gcp-store-and-forward-implementation.md)).
- **MCe never talks to the cloud directly.** All plant-to-cloud traffic goes through the Kestrel outbox and the DMZ proxy, so no service-account key sits in the plant ([ADR-023](../adr/ADR-023-gcp-network-identity-and-deployment.md)).
- **The Dataflow hot path subscribes only to live and alerts.** MDE takes everything, including backfill, for storage.
- **The DMZ holds three mirrors and proxies** (proxy, Git, and registry), and the cluster pulls from all of them.
