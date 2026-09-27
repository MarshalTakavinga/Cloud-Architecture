# Diagram: Google Distributed Cloud Track (Step 8)

Reference source (Mermaid) for [`docs/gcp-implementation.md`](../docs/gcp-implementation.md) and [ADR-021](../adr/ADR-021-gcp-gdc-cluster-topology.md) to [ADR-025](../adr/ADR-025-gcp-governance-delivery-and-vdi.md). A hand-drawn version will be produced from this source.

```mermaid
flowchart LR
    subgraph GIT["Git (VMs as code)"]
        MAN["VM · network · namespace manifests\nNetworkPolicy · recovery plans"]
    end

    subgraph GC["Google Cloud"]
        FLEET["Fleet · Config Sync · Policy Controller\nConnect gateway"]
        GKE["GKE landing zone\ndev/test · ML"]
        GCS[("Tier-1/2 vault copies\nBucket Lock")]
    end

    subgraph DC1["DC1"]
        direction TB
        subgraph GDC1["GDC bare metal (RHEL hosts)"]
            T0A["Tier-0 non-core cluster\nVM Runtime (KubeVirt)"]
            GENA["General cluster\nVMs + containers"]
        end
        ARR1[("CSI enterprise array")]
        subgraph ISL1["Certified island (Hyper-V)"]
            CORE1["Core banking app"]
            ORA1[("Oracle RAC")]
        end
        FW1["Site firewalls\n(L2-attached VM rules)"]
    end

    subgraph DC2["DC2"]
        direction TB
        GDC2["GDC clusters (standby)"]
        ARR2[("CSI array replica")]
        subgraph ISL2["Certified island (Hyper-V)"]
            CORE2["Core banking standby"]
            ORA2[("Oracle standby")]
        end
        ORCH["Bank-built orchestrator"]
        VAULT[("Vault ← Kasten + Veeam B&R")]
    end

    AVD["VDI: AVD / Windows 365\n(Azure)"]
    SENT["Sentinel"]

    MAN -- "Config Sync" --> GDC1
    MAN -- "re-apply in DR" --> GDC2
    ARR1 == "array replication" ==> ARR2
    ORA1 == "Data Guard" ==> ORA2
    CORE1 -- "Hyper-V Replica" --> CORE2
    ORCH -. "runs plans" .-> GDC2
    ORCH -. "runs plans" .-> ISL2
    GDC1 -. "Connect Agent\n(upgrades need it)" .-> FLEET
    GDC2 -. "Connect Agent" .-> FLEET
    GDC1 -. logs .-> SENT
    GENA -. "non-Tier-0 copies" .-> GCS
    T0A --- FW1
```

## How to read it

- **Two platforms in each site.** GDC runs everything the vendors support on KVM. The **certified island** (Hyper-V) runs core banking and Oracle, because the core vendor doesn't certify KVM ([ADR-022](../adr/ADR-022-gcp-certified-island.md)).
- **Git is the platform.** VMs, networks, and policies are manifests that Config Sync reconciles. In DR, the same manifests are re-applied to DC2 while the array replicas are promoted ([ADR-023](../adr/ADR-023-gcp-recovery.md)).
- **The Connect Agent line can be cut for a week, and VMs keep running and can be operated locally.** Cluster upgrades and node additions wait until it returns.
- **VDI sits in a third vendor's cloud** (Azure), because Horizon doesn't support KubeVirt.
