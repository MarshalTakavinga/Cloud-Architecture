# Diagram: Logical Architecture (Step 5)

Reference sources (Mermaid) for [`docs/logical-design.md`](../docs/logical-design.md) and [ADR-006](../adr/ADR-006-recovery-plan-model-and-readiness.md) to [ADR-008](../adr/ADR-008-zone-model-and-segmentation-as-code.md). They are platform-neutral: component IDs (P, C, D, R, O, L) match the table in `logical-design.md`, and Steps 6–9 map them onto each platform. Hand-drawn versions will be produced from these sources.

## 1. Component Model

```mermaid
flowchart TB
    subgraph CTRL["Control (govern centrally)"]
        C1["C1 Governance plane\ninventory · policy · patch compliance · RBAC"]
        C5["C5 Policy repo + pipeline\nGit → rendered rules, baselines, plans"]
        C6["C6 CMDB sync\n→ ServiceNow"]
        D1["D1 Platform API + catalog\nTerraform"]
        D2["D2 Image pipeline"]
        D3["D3 ServiceNow approvals"]
    end

    subgraph SITE1["DC1 — primary (operate locally)"]
        direction TB
        C2A["C2 Site manager"]
        C3A["C3 Local identity\nAD · PAM break-glass"]
        C4A["C4 Local repository"]
        C7A["C7 Licence service"]
        P1A["P1 Compute clusters\nZ0 · Z0-PCI · Z1 · Z2"]
        P3A["P3 Oracle cluster\n(licence boundary)"]
        P4A["P4 SDN + microsegmentation"]
        P6A["P6 Kubernetes platform"]
        R4A[("R4 Immutable backups")]
    end

    subgraph SITE2["DC2 — independent standby (operate locally)"]
        direction TB
        C2B["C2 Site manager"]
        C3B["C3 Local identity"]
        C4B["C4 Local repository"]
        R3["R3 Recovery orchestrator\n+ daily readiness job"]
        P1B["P1 Compute clusters\nZ0 standby · Z1 · Z2"]
        P3B["P3 Oracle standby cluster"]
        P4B["P4 SDN + microsegmentation"]
        R4B[("R4 Immutable backups")]
        R5[("R5 Isolated vault\nZ-VAULT")]
        R6["R6 Clean room\nZ-IRE"]
    end

    subgraph OBS["Observability"]
        O1["O1 Telemetry → Sentinel\n(buffered locally)"]
        O2["O2 Capacity + cost"]
        O3["O3 Vuln + config scanning"]
    end

    L1["L1 Public-cloud landing zone"]

    C5 -- "rendered artifacts" --> C4A
    C5 -- "rendered artifacts" --> C4B
    D2 --> C4A
    D2 --> C4B
    D3 --> D1 --> C2A
    D1 --> L1
    C1 -. govern .-> SITE1
    C1 -. govern .-> SITE2
    C1 -. govern .-> L1
    C1 --> C6
    P3A == "R1 Data Guard" ==> P3B
    P1A -- "R2 platform replication" --> P1B
    R3 -. "runs plans" .-> P1B
    R4A --> R5
    R4B --> R5
    R5 --> R6
    SITE1 --> O1
    SITE2 --> O1
```

**How to read it:** everything inside the two site boxes is on the **local-autonomy contract**, meaning it must keep working with no cloud control plane. The control box *governs* (dotted lines) and *publishes rendered artifacts* into each site's local repository, but no Tier-0 operation depends on reaching it.

## 2. Tier-0 Recovery-Plan Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Owner as Service owner
    participant Orch as Recovery orchestrator (DC2)
    participant G0 as G0 Shared services (active in DC2)
    participant DB as G1 Oracle Data Guard
    participant MW as G2 Middleware
    participant APP as G3 App servers
    participant PAY as G4 Payments gateways
    participant NET as G5 Ingress + DNS + FedLine
    participant VAL as G6 Synthetic transactions

    Note over Orch: Daily readiness job: lag, DC2 capacity, firewall parity, replicas, images → DR-ready
    Owner->>Orch: Declare disaster / test (decision 1)
    Orch->>G0: Health check AD, DNS, PKI, HSM, PAM
    G0-->>Orch: Green
    Owner->>Orch: Approve switchover (decision 2)
    Orch->>DB: Switchover / failover
    DB-->>Orch: Open read-write, lag recorded (RPO evidence)
    Orch->>MW: Start queues, replay
    MW-->>Orch: Drained
    Orch->>APP: Start in dependency order
    APP-->>Orch: Health endpoints OK
    Orch->>PAY: Vendor procedures (automated)
    PAY-->>Orch: Test transactions pass
    Orch->>NET: Cut over ingress, DNS, FedLine path
    NET-->>Orch: External reachability OK
    Orch->>VAL: Balance inquiry, transfer, ACH test file
    VAL-->>Owner: Results for sign-off
    Note over Orch,Owner: Every group timestamped → evidence report vs 3 h budget (RTO ≤ 4 h)
```

**How to read it:** the service owner makes only two decisions (declare, approve). Everything else is executed and timestamped by the orchestrator in DC2, which is why the plan works with DC1 gone. Each arrow pair is a gate: the next group doesn't start until the previous one reports healthy.
