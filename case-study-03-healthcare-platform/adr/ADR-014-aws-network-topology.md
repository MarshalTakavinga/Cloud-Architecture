### ADR-014: AWS network topology

**Context:**
The logical design carries forward Meridian's existing hub-and-spoke mental model, platform-neutral. AWS offers two realistic ways to implement that shape: a central AWS Transit Gateway peering multiple VPCs with a shared inspection point, or AWS Cloud WAN, a managed global network service aimed at large-scale, many-region, many-site connectivity — the AWS-side analog to the Virtual WAN vs. traditional hub-and-spoke choice ADR-007 made for Azure.

**Options considered:**
- Transit Gateway hub-and-spoke: a Transit Gateway as the routing hub, with an Inspection VPC (AWS Network Firewall) and application/data VPCs attached as spokes
- Full-mesh VPC peering: every VPC peered directly to every other VPC, no central hub
- AWS Cloud WAN: a Microsoft Virtual WAN-equivalent managed global network, automating routing and branch/site connectivity at scale

**Decision:** Transit Gateway hub-and-spoke, with a dedicated Inspection VPC hosting AWS Network Firewall as the hub.

**Rationale:**
Full-mesh VPC peering doesn't scale past a handful of VPCs — every new spoke needs a peering connection (and route table entries) to every existing spoke, and peering connections can't provide centralized traffic inspection, since traffic between two peered VPCs never passes through a third. That directly conflicts with the Zero Trust, inspect-everything posture ADR-002 established. AWS Cloud WAN earns its cost and complexity at a scale this workload doesn't have yet — many regions, many branch sites connecting directly into the cloud network, or Microsoft-managed routing across dozens of VPCs — the same reasoning ADR-007 used to reject Azure Virtual WAN. Meridian's AWS footprint for this case study is a primary region and one paired DR region, with clinics still connecting via existing site-to-site links during migration. Transit Gateway with a dedicated Inspection VPC gives full control over firewall and routing configuration at materially lower cost and complexity than Cloud WAN, and is the better-understood, more commonly deployed pattern for a workload at this scale.

**Trade-off:**
If Meridian's AWS footprint grows substantially — many more regions, or clinics connecting directly into AWS instead of through a central hub — a self-managed Transit Gateway topology becomes harder to operate by hand than Cloud WAN would have been. Named explicitly as a re-evaluation point, the same posture ADR-007 took: if the number of spokes or regions grows past what one team can manage manually, revisit this decision.

**Status:** Proposed

---

**A structural note worth naming explicitly.** AWS's isolation boundary for this kind of workload separation is the **account**, not a resource inside a shared account the way an Azure subscription is inside a tenant. Azure's Landing Zone pattern (ADR-007/`azure-implementation.md` §4.2) uses management groups holding multiple subscriptions; the AWS-native equivalent is **AWS Organizations** with **AWS Control Tower**, using **Organizational Units (OUs)** holding multiple **accounts**. In practice this design goes a step finer than a single account per environment: the Workloads OU splits Production into two accounts — one holding the Application VPC, one holding the Data VPC, so compute and data have independent account-level blast-radius and IAM boundaries — plus a Non-Production account, while the Infrastructure OU holds a Network account for the shared Inspection VPC. The paired DR region in us-west-2 mirrors that same four-account pattern rather than collapsing into a single DR account: a DR Production account for the DR Application VPC, a DR Production account for the DR Data VPC, a DR Network account for the DR Inspection VPC, and a DR Shared Services account for cross-cutting DR tooling (monitoring/logging, backup). Eight workload/network accounts across both regions in total, not three. This is a genuine model difference between the two platforms, not just different terminology for the same thing, and it's why the network design below treats VPC-to-VPC connectivity across accounts as a first-class concern (Transit Gateway supports cross-account attachments via AWS Resource Access Manager) rather than an afterthought.

See [`../docs/aws-implementation.md`](../docs/aws-implementation.md) §4 / §4.2 for the full VPC/subnet addressing plan and account structure this topology implements, and [`../diagrams/aws-network-topology-hub-spoke.png`](../diagrams/aws-network-topology-hub-spoke.png) / `diagrams/aws-network-addressing.png` / `diagrams/aws-deployment-architecture.png` for the topology, addressing, and end-to-end diagrams.
