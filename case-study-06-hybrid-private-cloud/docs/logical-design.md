# Step 5: Vendor-Neutral Logical Design

## Purpose

This step turns [Step 4](architecture-options-and-styles.md)'s style into **logical components**, independent of platform, and defines four structures every track must implement:
- the **zone model**
- the **recovery-plan model**
- the **Oracle cluster pattern**
- the **local-autonomy contract** (what "operate locally" means component by component)

Steps 6–9 map each component onto VCF, Azure Local + Arc, Google Distributed Cloud, and OpenStack, and flag where a platform cannot meet a component's contract.

## Logical Components (26)

| # | Component | Responsibility | Must work disconnected? (NFR-3) |
|---|---|---|---|
| **Platform** | | | |
| P1 | Compute clusters | Run VMs per zone. Rolling maintenance without a Tier-0 outage (NFR-2) | **Yes** |
| P2 | Storage | Block storage for VMs and databases, meeting p99 ≤ 2 ms writes for Oracle (NFR-4). Either hyperconverged or external array | **Yes** |
| P3 | Oracle clusters | Dedicated, licence-bounded clusters for Oracle ([ADR-007](../adr/ADR-007-oracle-cluster-and-licence-boundary.md)) | **Yes** |
| P4 | Software-defined network + microsegmentation | Zones, east-west default deny in Tier 0 and PCI, rules generated from policy as code ([ADR-008](../adr/ADR-008-zone-model-and-segmentation-as-code.md)) | **Yes** (enforcement is local; rule *changes* may wait) |
| P5 | Site edge | North-south firewalls, DC interconnect with quality-of-service classes for replication, and ingress for the digital-banking SaaS | **Yes** |
| P6 | Kubernetes platform | A conformant cluster service run by the platform team. It replaces the Rancher clusters | Tier-2 workloads only; Tier-0 VMs don't depend on it |
| **Control** | | | |
| C1 | Governance plane | Inventory (owner, tier, data class), policy as code, patch compliance, role-based access through Entra ID, across both sites and the landing zone | No (it governs; it doesn't operate) |
| C2 | Site manager | VM lifecycle, host maintenance, and console, for each site | **Yes** |
| C3 | Local identity | On-premises AD for platform administration, with break-glass accounts vaulted in PAM | **Yes** |
| C4 | Local repository | Images, OS patches, platform updates, and container images for each site | **Yes** |
| C5 | Policy repository and pipeline | Git plus a pipeline that renders firewall rules, baselines, and recovery plans | Rendering can wait. The rendered artifacts are held locally in C4 |
| C6 | CMDB sync | A daily reconciliation from C1 to ServiceNow (NFR-8) | No |
| C7 | Licence service | Whatever the platform needs to stay licensed while disconnected | **Yes, for longer than 7 days**. Checked per track |
| **Delivery** | | | |
| D1 | Platform API and catalog | Standard products through Terraform. Approvals in ServiceNow ([ADR-005](../adr/ADR-005-platform-api-and-portability.md)) | No (Tier-0 changes are frozen during a disconnect) |
| D2 | Image pipeline | Golden Windows and RHEL images with CIS baselines and signed provenance, published to C4 | No |
| D3 | Service catalog integration | ServiceNow request, approve, and record | No |
| **Resilience** | | | |
| R1 | Database replication | Oracle Data Guard from DC1 to DC2, with transport sized for the batch peak | **Yes** |
| R2 | Platform replication | Replication of stateful application VMs from DC1 to DC2 | **Yes** |
| R3 | Recovery orchestrator | Runs recovery plans as code ([ADR-006](../adr/ADR-006-recovery-plan-model-and-readiness.md)). Its **instance in DC2** can run with DC1 lost | **Yes** |
| R4 | Backup, immutable local | Local immutable copies in each DC | **Yes** |
| R5 | Isolated vault | A separate administrative domain with time-locked retention ([ADR-003](../adr/ADR-003-cyber-recovery-vault-and-isolated-recovery.md)) | **Yes** (it is built to be isolated) |
| R6 | Clean-room recovery environment | Restore, scan, and validate Tier 0 in DC2 | **Yes** |
| **Observability and security** | | | |
| O1 | Telemetry pipeline | Platform and guest logs and metrics to Microsoft Sentinel, **buffered locally** during a disconnect | Buffers locally |
| O2 | Capacity and cost reporting | Capacity per zone, and cost per business service (NFR-10) | No |
| O3 | Vulnerability and configuration scanning | CIS and vulnerability scanning of hosts and guests | Local scans continue |
| **Public cloud** | | | |
| L1 | Landing zone | Accounts or subscriptions, guardrails, private connectivity, and vault storage for Tier 1 and Tier 2 | Not applicable |

**The rule this table encodes:** anything marked **Yes** must run from components inside the bank's two sites, with local identity. That is the *local-autonomy contract*, and it is what the disconnected-week test in Steps 6–9 checks.

## The Zone Model ([ADR-008](../adr/ADR-008-zone-model-and-segmentation-as-code.md))

| Zone | Contents | East-west policy | Reachable from |
|---|---|---|---|
| **Z0: Tier 0** | Core banking application and database, payments gateways, API layer | **Default deny.** Allow lists per application tag | Z0-DMZ (API ingress), management, and the Tier-1 services named in policy |
| **Z0-PCI: Card-data environment** | Card management, HSM management | **Default deny.** PCI DSS 4.0.1 scope boundary | Z0 on named flows only |
| **Z0-DMZ** | API ingress for the digital-banking SaaS, FedLine connectivity | Deny by default. Inspected ingress only | Internet (via the site edge), Federal Reserve networks |
| **Z1: Tier 1** | Loan origination, treasury, fraud, identity, PKI, file transfer | Allow lists per application | Z0 and Z2 on named flows |
| **Z2: Tier 2** | Branch services, internal applications, reporting | Coarse rules per application group | Users, Z1 |
| **Z-MGMT** | Site managers, repositories, orchestrator, PAM jump hosts | Administrators through PAM only | PAM |
| **Z-VAULT** | The isolated vault | **No inbound from production.** The vault pulls | None from production |
| **Z-IRE** | The clean room | Isolated. Opened only by a recovery decision | None by default |

**Segmentation is generated, not hand-written.** Rules are expressed as intent in Git ("core-banking-app may reach core-banking-db on 1521"), rendered by the pipeline (C5) into each site's rule base, and **applied identically to DC1 and DC2**. A parity check compares the two sites' effective rules every day. This is the direct fix for the missing DC2 rules that broke the May 2026 failover. It also makes **both** sites PCI-segmented, where today only DC1 is.

## The Recovery-Plan Model ([ADR-006](../adr/ADR-006-recovery-plan-model-and-readiness.md))

Each Tier-0 and Tier-1 **business service** has one recovery plan in Git. A plan is an ordered set of **recovery groups**:

| Group | Contents | Gate to the next group |
|---|---|---|
| G0: Shared services (always active in DC2) | AD, DNS, PKI, HSM, PAM, time | Health checks are green. These services are never "recovered", because they run active in both sites |
| G1: Databases | Data Guard switchover or failover | Database open read-write, and the lag at failover recorded (RPO evidence) |
| G2: Middleware and integration | Message queues, integration services | Queues drained or replayed |
| G3: Application servers | Started in dependency order from replicas or images | Application health endpoints respond |
| G4: Payments gateways | Vendor-specific procedures, wrapped as automation | Vendor test transactions pass |
| G5: Ingress and network cutover | API ingress, DNS, and FedLine path in DC2 | External reachability confirmed |
| G6: Business validation | Synthetic transactions (balance inquiry, internal transfer, ACH file test) | Service owner signs off |

**Continuous DR readiness.** Recovery plans are not just run at test time. A **daily readiness job** checks:
- replication lag against the RPO
- the reserved Tier-0 capacity in DC2
- firewall parity between the sites
- that every VM in the plan still exists and is replicated
- that images and patches are present in DC2's local repository

It reports **"DR-ready" or "not DR-ready"** per service. Any Tier-0 change that breaks readiness fails the change.

**RTO evidence.** The orchestrator timestamps every group. Test reports compare actual times against the 3-hour budget ([ADR-002](../adr/ADR-002-recovery-as-code-active-standby.md)) and become MRA evidence.

## The Oracle Cluster Pattern ([ADR-007](../adr/ADR-007-oracle-cluster-and-licence-boundary.md))

- Oracle runs **only on dedicated physical clusters**, in both sites, sized to Oracle's needs.
- The **licence boundary is the physical cluster**. Under Oracle's partitioning policy, most hypervisors count as *soft* partitioning, so every core in a cluster that can run Oracle is licensed. Oracle's processor licences count **cores × 0.5** (the core factor for current Intel and AMD processors).
- **Today:** 640 cores (6 + 4 hosts) = **320 processor licences**. The Data Guard standby in DC2 is licensed as well.
- **Design rules for every track:**
  - No live migration of Oracle VMs outside the Oracle cluster. This is enforced by the platform, not by a runbook.
  - No shared management or automation that could place Oracle VMs elsewhere.
  - The cluster boundary is visible in the governance plane and audited monthly.
  - **Any change of hypervisor is reviewed with Oracle licensing specialists before the order.** Some KVM-based designs can claim *hard* partitioning, which could *reduce* the count, while a careless design can *increase* it.
- **Consolidation lever:** fewer, faster cores. The refresh can reduce the licensed core count if the batch window (NFR-4) still holds. Step 13 tests this.

## Six End-to-End Flows

1. **Provision a standard VM (NFR-9):**
   - ServiceNow request, then policy check (auto-approved for Tier 2).
   - Terraform runs against the platform API (D1), using a golden image (C4).
   - Zone rules are applied by tag (P4), the VM is registered in the governance plane (C1), and the CMDB is synced (C6).
   - **Target: under 1 hour.**
2. **Monthly patching:**
   - The image pipeline builds a new image.
   - Guests are patched from the local repository in waves (Tier 2, then Tier 1, then Tier 0 in a maintenance window).
   - Compliance is reported to C1. Rollback uses a snapshot or the previous image.
3. **Planned Tier-0 failover (test):**
   - The service owner declares the test.
   - The orchestrator (R3) runs G0–G6, timestamps each group, and publishes the evidence report.
   - Failback follows the same plan in reverse.
4. **Unplanned DC1 loss:**
   - The DC2 orchestrator instance runs the plan with DC1 unreachable, using local identity and repository.
   - Data Guard fails over, with the lag recorded.
5. **Destructive cyberattack:**
   - Production is isolated.
   - The vault (R5) restores the last clean Tier-0 copy into the clean room (R6).
   - The copy is scanned and validated, released to rebuilt production, and replayed from the core system's transaction journals where available.
6. **Cloud control plane unreachable for 7 days (the disconnected-week drill):**
   - Governance views go stale and the central policy update queue waits.
   - Every **Yes** component keeps operating.
   - A Tier-0 patch and a Tier-0 failover are both executed during the drill as proof.

## Diagram

See [`diagrams/logical-architecture.md`](../diagrams/logical-architecture.md) for the component model and the recovery-plan sequence (Mermaid reference sources, to be hand-drawn).

## What Each Platform Track Must Answer (Steps 6–9)

1. **Core banking certification** for its hypervisor. If it isn't certified, the track needs a certified island.
2. **Oracle:** the partitioning treatment and the resulting licence count.
3. **Horizon VDI** support, or a desktop alternative.
4. **Backup:** Veeam (or equivalent) support, immutability, and vault integration.
5. **The disconnected-week test:** each **Yes** component in the table above, *plus the licence service (C7)*.
6. **Microsegmentation** in both sites, and whether it costs extra.
7. **Kubernetes** (P6) and the platform API (D1), with a Terraform provider.
8. **Migration tooling** from vSphere 8, with change-block tracking and warm migration.
9. **Governance reach:** does C1 cover the public-cloud landing zone, and which cloud pairs naturally with the track?
