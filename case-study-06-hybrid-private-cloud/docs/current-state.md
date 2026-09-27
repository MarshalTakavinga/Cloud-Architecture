# Current-State Architecture

A current-state diagram is still to be drawn. Sections 1–5 map onto the usual facilities → compute and storage → workloads → operations → security layers.

## 1. Facilities and Network

| Site | Role | Notes |
|---|---|---|
| **DC1**, near Pittsburgh (owned) | Primary for every Tier-0 and Tier-1 system | Tier III-class facility, built 2011. UPS and generator refreshed in 2022 |
| **DC2**, Columbus, OH (colocation) | Recovery site; also runs some Tier-2 workloads active-active | 12 racks under a contract that runs to 2030. About 290 km from DC1 |
| **145 branches** | Thin sites with no local servers | SD-WAN (dual broadband + LTE), thin clients on VDI, and branch printers and cash recyclers on segmented VLANs |

- **DC1–DC2 links:** two diverse 10 Gb/s carrier circuits. The distance and the latency (about 4 ms round trip) rule out synchronous storage replication for Oracle, so replication is asynchronous.
- **Internet and cloud:** internet egress from both DCs through next-generation firewalls. There is **no private connection to any public cloud**. Microsoft 365 and Sentinel traffic goes over the internet.
- **Segmentation:** VMware NSX distributed firewall in DC1 only, used to isolate the PCI card-data environment. Everywhere else, segmentation is by VLAN and perimeter firewall.

## 2. Compute and Storage

| Cluster group | Hosts | Cores per host | Total cores | Bought | End of support |
|---|---|---|---|---|---|
| General-purpose, DC1 (4 clusters) | 26 | 2 × 24 = 48 | 1,248 | 2020 | **Dec 2027** |
| General-purpose, DC2 (3 clusters) | 18 | 2 × 24 = 48 | 864 | 2020 | **Dec 2027** |
| Oracle cluster, DC1 (dedicated for Oracle licensing) | 6 | 2 × 32 = 64 | 384 | 2023 | 2028+ |
| Oracle cluster, DC2 (standby) | 4 | 2 × 32 = 64 | 256 | 2023 | 2028+ |
| VDI (Horizon), DC1 and DC2 | 12 | 2 × 32 = 64 | 768 | 2023 | 2028+ |
| vSAN clusters (newer general-purpose), DC1 and DC2 | 10 | 2 × 32 = 64 | 640 | 2023 | 2028+ |
| **Total** | **76** | | **4,160** | | |

- **Storage:**
  - a DC1 Fibre Channel array (~480 TB usable) for Oracle and core banking, **end of support December 2027**
  - a DC2 array (~360 TB) receiving asynchronous array replication
  - vSAN on the newer clusters (~600 TiB raw)
  - a backup target (see section 4)
- **VMware stack (VCF subscription, March 2024 – March 2027):**
  - vSphere 8, vCenter per site
  - vSAN
  - NSX (DC1 PCI zone only)
  - Aria Operations
  - **Site Recovery Manager**, protecting only about 400 VMs
  - vSphere Replication

  Most of the other VCF components the subscription includes (VCF Operations automation, VCF's Kubernetes service) are **licensed but unused**.
- **Horizon VDI:** 1,400 desktops (contact center, branch back office, operations). Horizon is licensed separately from **Omnissa**, the former VMware end-user computing business, now independent.

## 3. Workloads

About **2,400 VMs**: Windows Server about 58%, RHEL about 34%, and appliances and other operating systems about 8%.

| Tier | Examples | VMs | Recovery objective (policy) | Achieved in the May 2026 test |
|---|---|---|---|---|
| **Tier 0** | Core banking (application servers + Oracle 19c RAC), Fedwire (FedLine Advantage), ACH, FedNow/RTP gateway, card management (PCI), API layer used by digital banking | ~260 | RTO 4 h / RPO 15 min | **RTO 11 h 40 min / RPO 35 min** |
| **Tier 1** | Loan origination, treasury management, fraud monitoring, AD/Entra Connect, PKI, file transfer, data warehouse (SQL Server) | ~520 | RTO 8 h / RPO 1 h | Not fully tested |
| **Tier 2** | Branch services, internal apps, reporting, dev/test | ~1,620 | RTO 24 h / RPO 24 h | Restore from backup |

- **Vendor appliances:** about **120 VMs** are vendor-supplied images, such as the payments gateways, HSM management, and the call-center platform. Each vendor certifies specific hypervisors.
- **Core banking platform support:** the core vendor **certifies VMware vSphere and Microsoft Hyper-V** (which includes Hyper-V-based Azure Local) for its application and database tiers. KVM-based hypervisors are described as "on the roadmap" in its 2026 platform statement. This is a hard constraint, carried into every track (`requirements.md`).
- **Oracle licensing:** Oracle is licensed per processor on the **dedicated Oracle clusters** (640 cores across both sites). Under Oracle's partitioning policy, VMware and Hyper-V are treated as *soft* partitioning, so every core in a cluster that could run Oracle must be licensed. Moving Oracle to a different hypervisor or cluster design changes the licence count, and that is a contract risk, not only a technical one.
- **Kubernetes:** three **Rancher RKE2** clusters (about 40 nodes on VMs) run the digital-lending APIs and the mobile back-end. The digital team built and runs them. They sit outside infrastructure patching and monitoring.
- **Batch:** the core banking nightly batch runs 23:00–02:00 and must finish before the 02:00 ACH window. In peak months it overruns by 20–40 minutes.

## 4. Operations

- **Team:** 24 infrastructure and operations staff: 14 VMware and Windows, 4 storage and backup, 3 Linux, and 3 automation, whose scripting is PowerCLI and some Ansible. Separately there are 9 network engineers and 12 in security operations.
- **Provisioning:** requests go through ServiceNow tickets to manual builds from templates. The average is **12 business days** per VM. There is no API, no self-service, and no infrastructure as code.
- **Patching:** ESXi and vCenter are patched quarterly. Guest operating systems are patched monthly through WSUS/SCCM for Windows and Satellite for RHEL. **About 9% of VMs** are missing from both tools, which is the inventory gap the examiners cited.
- **Backup:** Veeam backs up to a deduplicating appliance in each DC, with weekly tapes sent offsite. **Immutability exists only for Tier 0**, on hardened Linux repositories. There is no isolated recovery environment.
- **Disaster recovery:** SRM covers about 400 VMs. Tier-0 failover depends on **a 140-step runbook** that mixes SRM, Oracle Data Guard switchover, DNS and firewall changes, and manual application checks. The May 2026 test failed mainly on runbook steps: the order of dependencies, firewall rules missing in DC2, and Oracle redo transport lagging under batch load.
- **Monitoring:** Aria Operations for the infrastructure, a separate APM tool for core banking, and **Microsoft Sentinel** as the SIEM. The CMDB in ServiceNow is populated by discovery and is incomplete.

## 5. Identity and Security (As-Is)

- **Identity:** Entra ID for the workforce, with on-premises Active Directory synchronized. vCenter uses AD integration. Privileged access goes through a PAM vault, but about 30 local and break-glass accounts on hosts and appliances are outside it.
- **Security program:** aligned to the FFIEC Cybersecurity Assessment Tool and its successor NIST CSF 2.0 profile, and to PCI DSS 4.0.1 for the card-data environment. There is an annual penetration test.
- **The 2025 AWS proof-of-concept account:** opened by the digital-lending team for a machine-learning prototype. It has no SSO (only IAM users), no log forwarding to Sentinel, and no review of its data classification. It holds extracts described as masked, which a 2026 internal review showed could be re-identified. It is carried as a named governance risk, like the ad hoc cloud accounts in Case Studies 2, 4, and 5. It is **not** a vote for AWS.

## 6. Cost Baseline (infrastructure platform, annual)

| Item | Annual cost |
|---|---|
| VMware Cloud Foundation subscription (March 2024 – March 2027) | ~$1.25M |
| VCF renewal quote, April 2027 – March 2030 (3-year) | **~$1.65M / yr** (before any core true-up) |
| Omnissa Horizon (VDI) | ~$0.35M |
| Windows Server Datacenter (Enterprise Agreement with Software Assurance) | ~$0.60M |
| Red Hat Enterprise Linux subscriptions | ~$0.40M |
| Veeam and backup-appliance support | ~$0.30M |
| Hardware and storage maintenance (all hosts and arrays) | ~$0.55M |
| DC2 colocation and DC1 facility share | ~$1.60M |
| **Recurring infrastructure platform run cost (current)** | **~$5.05M / yr** |
| Hardware refresh due by December 2027 (44 hosts + DC1 Fibre Channel array), like for like | **~$4.2M one-time** |

Staff costs, the Oracle licences, and the core banking licence are excluded. They don't change with the choice of hypervisor, except for the Oracle licence-count risk described in section 3. This baseline, with the VCF renewal quote replacing the current subscription line, is the **status-quo path** that driver 2 compares against.

## 7. What This Case Study Inherits

The estate *works*. Core banking processes every night, the branches open every morning, and examiners get their reports. What it cannot do is:
- **prove its own recovery**
- **account for everything it runs**
- **offer delivery teams anything faster than a ticket**
- **negotiate its largest software renewal from a position of strength**

As in Case Studies 2, 4, and 5, this is a capability and governance gap, not a system in crisis. **The 31 March 2027 VMware renewal date and the December 2027 hardware end of support** are what turn it into a deadline.
