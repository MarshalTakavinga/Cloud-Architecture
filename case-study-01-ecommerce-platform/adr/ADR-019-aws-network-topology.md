### ADR-019: AWS multi-region network topology

**Context:**
This design runs three simultaneously-active regions (US, EU, APAC), every region live all the time for latency, not for failover (`architecture-options-and-styles.md` §3). Three independently-active regions, each needing to reach a shared cross-region resource (the Global Catalog primary in US, per ADR-015) and each wanting consistent egress-security posture, is a connectivity problem that grows combinatorially if solved with pairwise connections rather than a hub.

**Options considered:**
- Three independent VPCs, one per region, manually VPC-peered pairwise wherever cross-region connectivity is needed.
- AWS Transit Gateway, one per region, connected via inter-region Transit Gateway peering.
- One VPC per region with no internal subnet segmentation (no dedicated Checkout & Payment subnet).

**Decision:**
AWS Transit Gateway deployed in each of US, EU, and APAC, connected via inter-region Transit Gateway peering, with one VPC per region hosting that region's ECS Fargate services (ADR-013), Step Functions/Lambda saga compute (ADR-016), and database resources (ADR-014, ADR-015).

**Rationale:**
Manual pairwise VPC peering is rejected for the same non-transitivity reason ADR-011 rejected it on Azure: peering doesn't transit on AWS any more than it does on Azure's own peering primitive, so a EU-to-APAC connection needs its own separate peering connection alongside EU-to-US and APAC-to-US, an every-pair-connected mesh that grows combinatorially as more regions are added. This design needs three regions talking to a shared resource *continuously*  every region's Storefront & Catalog reads from its local Global Catalog replica, fed by ongoing replication from the US primary (ADR-015)  not the occasional, failover-triggered connectivity a two-region hub-and-spoke is built for. Transit Gateway inter-region peering solves this the same way Virtual WAN's regional hubs do on Azure: each region's Transit Gateway is a hub, inter-region peering connections between them give any-to-any regional reachability without a full peering mesh, and traffic between peered Transit Gateways travels over AWS's own backbone rather than the public internet. An unsegmented single VPC per region is rejected for the same PCI-isolation reason ADR-011 rejected a flat VNet on Azure: it gives Checkout & Payment's isolated network segment (ADR-013) nothing real to be isolated from within its own region.

**Trade-off:**
Transit Gateway is a managed, higher-abstraction product than self-assembled VPC peering, with its own per-attachment and per-GB-processed cost  Solstice trades some fine-grained routing control for AWS operating the inter-region backbone connectivity. Accepted for the identical reason ADR-011 accepted the equivalent trade-off on Azure: a three-way (or more) peering mesh maintained by a 22-person engineering org already carrying the compute/database/messaging surface area from ADR-013 through ADR-018 is real, avoidable operational load.

One trade-off worth stating plainly rather than smoothing over: unlike Azure's Virtual WAN, which bundles an integrated Azure Firewall into every Secured Virtual Hub by default, AWS Transit Gateway is purely a routing and connectivity layer. Egress inspection and filtering requires a separate, explicitly-deployed AWS Network Firewall (or third-party appliance) in a dedicated inspection VPC attached to each region's Transit Gateway. This isn't a reduction in achievable security posture relative to the Azure track  the end state is equivalent  but it is an extra resource this ADR has to call out and provision explicitly rather than getting bundled into the hub product, and it should be sized and priced as its own line item in the migration-roadmap and cost-analysis stages.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Topology | AWS Transit Gateway, one per active region |
| Inter-region connectivity | Transit Gateway inter-region peering  US↔EU, US↔APAC, EU↔APAC  any-to-any once peered, over AWS's backbone, no manual VPC peering |
| VPC per region | One VPC, subnets for: Storefront & Catalog/Cart ECS service (ADR-013), Checkout & Payment ECS service (ADR-013), Order Orchestration Lambda/Step Functions (ADR-016), database subnets (ADR-014/ADR-015), API Gateway VPC Link target subnet (ADR-020) |
| Egress control | AWS Network Firewall deployed in a dedicated inspection VPC attached to each region's Transit Gateway; all spoke-VPC egress routed through it  no direct-to-internet path from any application subnet |
| Cross-region traffic in practice | Global Catalog cross-region read replication (US primary → EU/APAC replicas, ADR-015) is the only steady-state cross-region data path; Cart/Checkout/Orders/Event Bus traffic (ADR-014, ADR-017) stays entirely within its own region by design |

**Status:** Approved

---

See [diagram](../diagrams/aws-network-topology.png).
