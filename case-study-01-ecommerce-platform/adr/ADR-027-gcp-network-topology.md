### ADR-027: GCP multi-region network topology

**Context:**
This design runs three simultaneously-active regions (US, EU, APAC), every region live all the time for latency, not for failover (`architecture-options-and-styles.md` §3). Three independently-active regions, each needing to reach a shared cross-region resource (the Global Catalog primary in US, per ADR-023) and each wanting consistent egress-security posture, is exactly the connectivity problem ADR-011 (Azure) and ADR-019 (AWS) both solved with a regional-hub product.

**Options considered:**
- Multiple regional VPC networks, one per region, manually peered pairwise wherever cross-region connectivity is needed  mirroring the pattern the other two platforms required.
- A single global Google Cloud VPC network (custom-mode), with regional subnets in US, EU, and APAC.
- Shared VPC (GCP's mechanism for sharing one VPC's networking across multiple projects)  not applicable here, since this workload runs in a single project/environment.

**Decision:**
A single global Google Cloud VPC network (custom-mode), with regional subnets in the US, EU, and APAC regions, each hosting that region's Cloud Run services (ADR-021), Cloud Workflows step compute (ADR-024), and Cloud SQL private-IP database resources (ADR-022, ADR-023). No inter-region peering, hub, or transit gateway of any kind is provisioned or needed.

**Rationale:**
This is the headline platform difference in this ADR, worth stating plainly rather than mechanically restating the Azure/AWS pattern: unlike Azure VNets and AWS VPCs, which are **regional** resources requiring a hub product (Virtual WAN, Transit Gateway) or a peering mesh for any-to-any inter-region reachability, a Google Cloud VPC network is a **global** resource  its subnets can live in any region, and resources in different regional subnets of the same VPC reach each other directly over Google's private backbone by default, with no peering connection, no hub, and no per-region-pair connection to provision, monitor, or pay for. The "combinatorial peering mesh" problem ADR-011 and ADR-019 both had to solve by introducing a hub product simply doesn't exist on GCP at this scale  a genuine structural simplification, not a smaller version of the same problem restated. Multiple regional VPCs manually peered was considered and rejected specifically because it would import AWS's and Azure's problem onto a platform that doesn't have it, adding peering connections and route management for no benefit a single global VPC doesn't already provide by default. Shared VPC is rejected as not applicable  it solves multi-project network sharing within an organization, a different problem than this single-workload deployment has.

**Trade-off:**
Stated honestly rather than smoothed over: a single global VPC concentrates the entire network's routing and firewall-policy surface into one resource. GCP's hierarchical firewall policies and VPC firewall rules do support per-subnet and per-tag scoping  so Checkout & Payment's isolated subnet still gets structurally enforced isolation, the same as the other two tracks' dedicated-subnet approach  but a misconfigured global firewall rule has a larger potential blast radius than a per-region hub's rule would, since there is no per-region hub boundary forcing deliberate provisioning of inter-region reachability the way ADR-011 and ADR-019's hub products did. The "any-to-any connectivity by default" strength is also a discipline requirement, not something the platform enforces structurally: default-deny firewall posture and deliberate per-tag scoping on every rule matter more here than they did on the other two tracks, where the hub product itself was the thing standing between regions until explicitly peered. Egress inspection and filtering also isn't automatically bundled here, the same honest gap ADR-019 named for AWS's Transit Gateway (which doesn't bundle a firewall the way Azure's Virtual WAN does)  except on GCP there isn't even a hub product to begin with, so egress control (Cloud NGFW or Secure Web Proxy, plus Cloud NAT for controlled internet egress) has to be explicitly deployed per region regardless.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Topology | Single global Google Cloud VPC network (custom-mode) |
| Inter-region connectivity | Native and default  any subnet in the VPC reaches any other subnet in the VPC over Google's private backbone, no peering or hub required |
| Regional subnets | One subnet set per region, for: Storefront & Catalog/Cart Cloud Run service (ADR-021), Checkout & Payment Cloud Run service (ADR-021), Order Orchestration Cloud Workflows step compute (ADR-024), Cloud SQL private-IP database resources (ADR-022, ADR-023), load-balancer backend connectivity (ADR-028) |
| Egress control | Cloud NGFW (or Secure Web Proxy) deployed per region, default-deny hierarchical firewall policy; Cloud NAT for controlled internet egress  no direct-to-internet path from any application subnet |
| Cross-region traffic in practice | Global Catalog cross-region read replication (US primary → EU/APAC replicas, ADR-023) is the only steady-state cross-region data path; Cart/Checkout/Orders/Event Bus traffic (ADR-022, ADR-025) stays entirely within its own region by design |

**Status:** Approved

---

See [diagram](../diagrams/gcp-network-topology.png).
