# Diagram: OpenStack Track (Step 9)

Reference source (Mermaid) for [`docs/openstack-implementation.md`](../docs/openstack-implementation.md) and [ADR-026](../adr/ADR-026-openstack-distribution-and-topology.md) to [ADR-030](../adr/ADR-030-openstack-operating-model-backup-and-vdi.md). A hand-drawn version will be produced from this source.

```mermaid
flowchart LR
    subgraph GIT["Git + Terraform + Ansible"]
        TF["Instances · networks · security groups\nrecovery plans"]
    end

    subgraph DC1["DC1 — OpenStack region A"]
        direction TB
        CP1["Control plane pods on OpenShift\nKeystone · Nova · Neutron/OVN · Cinder"]
        CMP1["KVM compute (RHEL)\nZ0 · PCI · General AZs\nOVN security groups"]
        CEPH1[("Ceph cluster")]
        OCP1["OpenShift on OpenStack\n(digital team)"]
        subgraph ISL1["Certified island (Hyper-V)"]
            CORE1["Core banking app"]
            ORA1[("Oracle RAC")]
        end
        SAT1["Satellite · AAP · local mirrors"]
    end

    subgraph DC2["DC2 — OpenStack region B (independent)"]
        direction TB
        CP2["Control plane (OpenShift pods)"]
        CEPH2[("Ceph cluster")]
        subgraph ISL2["Certified island (Hyper-V)"]
            CORE2["Core banking standby"]
            ORA2[("Oracle standby")]
        end
        ORCH["Bank-built orchestrator\nTerraform + Ansible"]
        VAULT[("Vault ← Trilio + Veeam")]
    end

    subgraph AZ["Azure"]
        ARC["Arc-enabled servers (guests)\nlanding zone · Sentinel"]
        AVD["VDI: AVD / Windows 365"]
    end

    PART["Managed-service partner\n(years 1–3)"]

    TF --> CP1
    CEPH1 == "RBD mirroring 5 min" ==> CEPH2
    ORA1 == "Data Guard" ==> ORA2
    CORE1 -- "Hyper-V Replica" --> CORE2
    ORCH -. "re-create instances\non mirrored volumes" .-> CP2
    ORCH -. "runs plans" .-> ISL2
    CMP1 -. "guest agents" .-> ARC
    PART -. operates .-> CP1
    PART -. operates .-> CP2
```

## How to read it

- **Nothing in either site needs a vendor cloud to operate.** The control planes, mirrors, and identity are all local, and a lapsed subscription removes support, not operations. This is the strongest disconnected-week result of the four tracks.
- **The island is the cost of KVM.** As on the GDC track, core banking and Oracle stay on certified Hyper-V ([ADR-027](../adr/ADR-027-openstack-certified-island-and-recovery.md)).
- **Recovery re-creates rather than replicates instances.** Ceph mirrors the volumes, and Terraform re-creates the instances in region B on the mirrored volumes.
- **The partner box is part of the design, not an afterthought** ([ADR-030](../adr/ADR-030-openstack-operating-model-backup-and-vdi.md)).
