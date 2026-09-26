# Diagram: AWS Implementation Architecture (Step 7)

Reference source (Mermaid) for the Step 7 diagram in [`docs/aws-implementation.md`](../docs/aws-implementation.md) and [ADR-012](../adr/ADR-012-aws-edge-platform.md) to [ADR-017](../adr/ADR-017-aws-network-identity-and-deployment.md). A hand-drawn version will be produced from this source, as with the other case studies. The same shape is deployed in us-east-2 (US/MX plants) and eu-central-1 (Plants 11–12).

```mermaid
flowchart LR
    subgraph PLANT["Plant (×10 US/MX · ×2 DE)"]
        direction TB
        L2["Level 2 OPC UA servers\n(+ protocol gateways)"]
        STN["Station / MES"]
        subgraph PAIR["Level 3 — active/passive pair + witness\n(Pacemaker/Corosync · DRBD protocol C)"]
            direction TB
            subgraph SWE["Greengrass v2 + SiteWise Edge (MQTT-enabled V3)"]
                OPC["IoT SiteWise OPC UA collector"]
                EMQX[["EMQX broker (UNS)"]]
                subgraph SM["Stream manager (File persistence)"]
                    S1[["genealogy · prio 1"]]
                    S2[["alerts · prio 2"]]
                    S3[["live · prio 3 · TTL 5 min"]]
                    S4[["history · prio 10\nexport off until outage"]]
                end
            end
            subgraph KB["Kestrel-built Greengrass components"]
                FEAT["P3 Feature extractor"]
                ANOM["P4 Anomaly detector (ONNX)"]
                REC["P5 Genealogy recorder\n+ SQLite serial index"]
                PUB["Lane publisher"]
                BFC["Backfill controller"]
                ACT["Model activation"]
            end
            TSDB[("P8 TimescaleDB\n30 days")]
        end
        subgraph DMZ["Level 3.5 — DMZ"]
            PROXY["HTTPS forward proxy\n(allowlist)"]
        end
        L2 -- "OPC UA read" --> OPC
        OPC --> EMQX
        FEAT --> EMQX
        EMQX --> ANOM
        EMQX --> PUB
        EMQX --> TSDB
        STN <--> REC
        REC --> S1
        ANOM --> S2
        PUB --> S3
        PUB --> S4
        BFC -. "enable export from seq n" .-> S4
        SM -- "priority export\n(bandwidth cap)" --> PROXY
        ACT -. "shadow → approve → active" .-> ANOM
    end

    COL["Columbus DC\n(MPLS hub · SAP ECC)"]

    subgraph AWS["AWS region (us-east-2 · eu-central-1 for DE)"]
        direction TB
        TGW["Transit Gateway\n+ VPC endpoints"]
        subgraph KDS["Kinesis Data Streams (on-demand)"]
            KG[["genealogy"]]
            KA[["alerts"]]
            KL[["telemetry-live"]]
            KB2[["telemetry-backfill"]]
        end
        NORM["Managed Flink: normalizer\n(dedupe · event time)"]
        HOT["Managed Flink: hot path\n(live + alerts only)"]
        SMK["SageMaker AI\n(endpoint · training · registry)"]
        SQS[["SQS FIFO"]]
        LAM["Lambda → SAP OData"]
        INF[("Timestream for InfluxDB\n90 days")]
        S3T[("S3 Tables (Iceberg)\n5 years · Athena")]
        BI["QuickSight · Managed Grafana\n(OEE)"]
        LDR["Lambda loader"]
        AUR[("Aurora PostgreSQL\ninsert-only + hash chain")]
        OL[("S3 Object Lock\ndigests + 15-yr archive")]
        IOT["IoT Core · Greengrass deployments\n· Device Management · Signer"]
    end

    PROXY -- "outbound only" --> COL
    COL -- "Site-to-Site VPN\n(DE plants: direct VPN to EU)" --> TGW
    TGW --> KDS
    KG --> LDR
    LDR --> AUR
    AUR --> OL
    KA --> HOT
    KL --> HOT
    KA --> NORM
    KL --> NORM
    KB2 --> NORM
    NORM --> INF
    NORM --> S3T
    S3T --> BI
    S3T --> SMK
    HOT <--> SMK
    HOT --> SQS
    SQS --> LAM
    LAM -- "PM notification" --> COL
    IOT -. "notify over outbound session;\nartifacts downloaded via proxy" .-> PAIR
```

## How to read it

- **Stream manager is the outbox.** The four lanes are four native streams with export priorities. The only Kestrel code on the lane path is the backfill controller, which just turns the `history` export on and off ([ADR-013](../adr/ADR-013-aws-store-and-forward-implementation.md)).
- **The whole Level 3 box is an active/passive pair.** HA comes from Pacemaker/DRBD, not from AWS. This is the track's main operational risk ([ADR-012](../adr/ADR-012-aws-edge-platform.md)).
- **`telemetry-backfill` feeds only the normalizer, never the hot path,** so ADR-005 is enforced by wiring.
- **The dotted line from IoT Core** is a notification over the plant's own outbound session. Artifacts are downloaded by the device through the DMZ proxy ([ADR-017](../adr/ADR-017-aws-network-identity-and-deployment.md)).
