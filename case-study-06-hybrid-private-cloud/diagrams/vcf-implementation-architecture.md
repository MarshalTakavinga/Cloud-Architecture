# Diagram: VCF Track Implementation (Step 6)

Reference source (Mermaid) for [`docs/vcf-implementation.md`](../docs/vcf-implementation.md) and [ADR-009](../adr/ADR-009-vcf-platform-and-domain-design.md) to [ADR-014](../adr/ADR-014-vcf-cloud-extension.md). A hand-drawn version will be produced from this source.

```mermaid
flowchart LR
    subgraph GIT["Bank-owned code (Git)"]
        POL["Zone intent · baselines"]
        PLANS["Recovery plans G0–G6"]
        TF["Terraform: NSX · vSphere · VCF Automation"]
    end

    subgraph DC1["DC1 — VCF 9.1 instance A"]
        direction TB
        MGMT1["Mgmt domain\nvCenter · NSX Mgr · VCF Ops (disconnected)\nVCF Automation · offline depot"]
        WD0A["Tier-0 + PCI domain\nvSAN ESA · vDefend DFW"]
        ORA1[("Oracle domain\nlicence boundary · vSAN ESA")]
        GENA["General domain Z1/Z2\nNSX VPCs · VKS clusters"]
        VDIA["VDI domain (Horizon)"]
        VEE1[("Veeam hardened repo")]
    end

    subgraph DC2["DC2 — VCF 9.1 instance B (independent)"]
        direction TB
        MGMT2["Mgmt domain\nvCenter · NSX Mgr · VCF Ops · Live Recovery"]
        WD0B["Tier-0 + PCI standby\nvDefend DFW (same rules)"]
        ORA2[("Oracle standby domain")]
        GENB["General domain Z1/Z2"]
        VAULT[("Veeam isolated vault\nseparate admin domain")]
        IRE["Live Recovery\non-prem clean room"]
    end

    subgraph AZ["Azure landing zone"]
        ARC["Arc-enabled servers\n(guest inventory · policy · patch reporting)"]
        SENT["Sentinel"]
        LZ["Dev/test · Tier-1/2 vault copies"]
    end

    BCOM["Broadcom licence portal\n(usage report every 180 days)"]
    SNOW["ServiceNow\napprovals · CMDB"]

    ORA1 == "Data Guard" ==> ORA2
    WD0A -- "Live Recovery\nvSAN→vSAN" --> WD0B
    GENA -- "Live Recovery" --> GENB
    PLANS -- "generated plans" --> MGMT2
    POL -- "rendered rules" --> WD0A
    POL -- "rendered rules" --> WD0B
    TF --> MGMT1
    SNOW --> TF
    VEE1 --> VAULT --> IRE
    WD0A -. "guest agents" .-> ARC
    GENA -. "guest agents" .-> ARC
    MGMT1 -. logs .-> SENT
    MGMT2 -. logs .-> SENT
    MGMT1 -. "offline usage file" .-> BCOM
    GENA -. "non-Tier-0 copies" .-> LZ
```

## How to read it

- **Two independent VCF instances.** Each site has its own management domain, so DC2 can operate and recover with DC1 gone. Only data crosses between them: Data Guard, Live Recovery replication, and backup copies.
- **Git is the source; the platforms receive rendered artifacts.** Zone rules go to both sites' vDefend firewalls, and recovery plans are generated into Live Recovery in DC2.
- **Azure sees guests, not the platform.** Arc-enabled vSphere doesn't support vCenter 9, so governance reaches Azure through guest agents (Arc-enabled servers).
- **The dotted line to Broadcom is the licence obligation.** A usage file goes out at least every 180 days. If it doesn't, or if the subscription lapses, workload operations stop ([ADR-012](../adr/ADR-012-vcf-control-plane-and-governance.md)).
