# Diagram: Azure Local + Azure Arc Track (Step 7)

Reference source (Mermaid) for [`docs/azure-implementation.md`](../docs/azure-implementation.md) and [ADR-015](../adr/ADR-015-azure-local-instance-topology.md) to [ADR-020](../adr/ADR-020-azure-vdi.md). A hand-drawn version will be produced from this source.

```mermaid
flowchart LR
    subgraph AZ["Azure (governance + landing zone)"]
        ARC["Azure Arc · Policy · Defender\nUpdate Manager (reporting) · Resource Graph"]
        SENT["Sentinel"]
        LZ["Landing zone\ndev/test · ML · Tier-1/2 vault (immutable Blob)"]
        AVDCP["AVD control plane"]
    end

    subgraph DC1["DC1 — Azure Local instances (connected, L1 + Hybrid Benefit)"]
        direction TB
        T0A["Tier-0/PCI instance\nlocally managed Hyper-V VMs\nDatacenter Firewall (on-prem SDN)"]
        ORA1[("Oracle instance\nlocally managed · S2D")]
        GENA["General instance\nArc VMs · NSGs · AKS on Azure Local"]
        VDIA["VDI instance\nAVD session hosts"]
        LOCA["Local ops: WAC · Failover Cluster Mgr\nPowerShell · AD · WSUS/Satellite"]
        VEE1[("Veeam hardened repo")]
    end

    subgraph DC2["DC2 — Azure Local instances (independent)"]
        direction TB
        T0B["Tier-0/PCI standby instance"]
        ORA2[("Oracle standby instance")]
        GENB["General instance"]
        ORCH["Bank-built orchestrator\nAnsible + PowerShell · Git plans"]
        VAULT[("Veeam isolated vault")]
        IRE["Clean-room Hyper-V cluster"]
    end

    ORA1 == "Data Guard" ==> ORA2
    T0A -- "Hyper-V Replica 30 s" --> T0B
    GENA -- "Hyper-V Replica 5 min\n(re-register after failover)" --> GENB
    ORCH -. "runs plans" .-> T0B
    VEE1 --> VAULT --> IRE
    T0A -. "Arc-enabled servers\n(guest agents)" .-> ARC
    GENA -. "Arc VM mgmt\n(portal / Terraform)" .-> ARC
    DC1 -. "30-day sync" .-> ARC
    DC2 -. "30-day sync" .-> ARC
    VDIA -. brokering .-> AVDCP
    GENA -. logs .-> SENT
    T0A -. logs .-> SENT
    GENA -. "non-Tier-0 copies" .-> LZ
```

## How to read it

- **Two kinds of VM on one platform.** Tier 0 and Oracle are **locally managed Hyper-V VMs**: they are operated from the "Local ops" box and reach Azure only through guest agents (dotted). Tier 1 and Tier 2 are **Arc-managed**, and their lifecycle runs through Azure. That split is how this track meets the invariant ([ADR-016](../adr/ADR-016-azure-tier0-local-management-mode.md)).
- **Every dotted line to Azure can be cut for a week without stopping Tier 0.** The 30-day sync only blocks *new* VMs. VDI brokering and Tier-1/2 lifecycle degrade, and both are acceptable for Tier 1.
- **The orchestrator in DC2 is bank-built,** because there is no packaged on-premises DR orchestrator for Azure Local ([ADR-017](../adr/ADR-017-azure-recovery.md)).
