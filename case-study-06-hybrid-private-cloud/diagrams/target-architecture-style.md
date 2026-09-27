# Diagram: Target Architecture Style (Step 4)

Reference source (Mermaid) for the Step 4 diagram in [`docs/architecture-options-and-styles.md`](../docs/architecture-options-and-styles.md) and [ADR-001](../adr/ADR-001-platform-strategy-and-workload-placement.md) to [ADR-005](../adr/ADR-005-platform-api-and-portability.md). It is platform-neutral: Steps 6–9 map each box onto VCF, Azure Local + Arc, Google Distributed Cloud, or OpenStack. A hand-drawn version will be produced from this source.

```mermaid
flowchart LR
    subgraph CP["Govern centrally (one plane)"]
        GOV["Inventory · policy as code · patch compliance\nRBAC via Entra ID"]
        API["Platform API + catalog\nTerraform · ServiceNow approvals"]
        PIPE["Image pipeline\nsigned golden images"]
    end

    subgraph DC1["DC1 Pittsburgh — primary (private cloud)"]
        direction TB
        T0A["Tier 0 zone\ncore banking · payments · cards · API layer"]
        ORA1[("Oracle cluster\nlicence-aware · primary DB")]
        T12A["Tier 1 / Tier 2 zones"]
        K8S1["Platform Kubernetes\n(replaces Rancher)"]
        LOC1["Local ops path\nAD · PAM break-glass · console · repo"]
        IMM1[("Immutable backup copies")]
    end

    subgraph DC2["DC2 Columbus — independent standby (private cloud)"]
        direction TB
        T0B["Tier 0 standby zone"]
        ORA2[("Oracle standby\nData Guard")]
        T12B["Tier 1 / Tier 2 zones\n(sheddable in failover)"]
        ORCH["Recovery orchestrator\nrecovery plans as code"]
        LOC2["Local ops path"]
        IMM2[("Immutable backup copies")]
        VAULT[("Isolated vault\nseparate admin domain · time-locked")]
        IRE["Clean-room recovery\nenvironment (Tier 0)"]
    end

    subgraph PUB["Public-cloud landing zone (governed)"]
        DEV["Dev/test · analytics · ML"]
        T2C["Tier 2 by choice"]
        CV[("Tier 1/2 vault copies\nobject lock · bank-held keys")]
    end

    NET["Network & firewall policy as code\n(identical in both sites)"]
    SIEM["Microsoft Sentinel · ServiceNow CMDB"]

    ORA1 == "Data Guard async\n≤ 15 min RPO" ==> ORA2
    T0A -- "platform replication /\nrebuild from image" --> T0B
    ORCH -. "dependency-ordered failover" .-> T0B
    NET -. applied .-> DC1
    NET -. applied .-> DC2
    IMM1 --> VAULT
    IMM2 --> VAULT
    VAULT --> IRE
    T12A -. "non-Tier-0 copies" .-> CV
    GOV -. "govern" .-> DC1
    GOV -. "govern" .-> DC2
    GOV -. "govern" .-> PUB
    API --> DC1
    API --> PUB
    PIPE --> API
    GOV --> SIEM
```

## How to read it

- **The two sites are independent.** DC2 is not a stretched extension of DC1. It has its own clusters, its own local operations path, and the recovery orchestrator. Only data crosses between the sites: Oracle Data Guard, platform replication, and backup copies ([ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md)).
- **Dotted "govern" lines are the central plane.** It sets policy, inventory, patch compliance, and access across both sites and the public-cloud landing zone. **None of the solid operational paths runs through it**, which is the invariant expressed as a picture ([ADR-004](../adr/ADR-004-govern-centrally-operate-locally.md)).
- **Network policy is generated once and applied to both sites.** That removes the firewall drift that broke the May 2026 failover.
- **The vault and the clean room are in DC2, behind their own administrative domain** ([ADR-003](../adr/ADR-003-cyber-recovery-vault-and-isolated-recovery.md)). Only non-Tier-0 vault copies go to the public cloud.
