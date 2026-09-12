### ADR-011: Azure multi-region network topology

**Context:**
This design runs three simultaneously-active regions (US, EU, APAC)  genuinely different from Case Study 3's network problem, which was one primary region plus one warm-standby paired region (ADR-007 there chose hub-and-spoke specifically for that two-region shape). `architecture-options-and-styles.md` §3 already named this distinction explicitly: Solstice's multi-region posture exists for latency, with every region live all the time, not for failover. Three independently-active regions, each needing to reach shared cross-region resources (the Global Catalog primary in US, per ADR-007) and each wanting consistent security posture, is a materially different connectivity problem than one primary plus one standby.

**Options considered:**
- Three independent hub-and-spoke VNet topologies, one per region, manually VNet-peered to each other where cross-region connectivity is needed (the same shape Case Study 3 used, extended to three regions).
- Azure Virtual WAN  Microsoft's managed, global network-as-a-service, with regional hubs automatically interconnected over Microsoft's backbone.
- A single flat global VNet with no regional segmentation.

**Decision:**
Azure Virtual WAN, with a regional hub in each of US, EU, and APAC, and a spoke VNet per region hosting that region's Container Apps environments (ADR-005, ADR-008) and database resources (ADR-006, ADR-007).

**Rationale:**
A flat, unsegmented global VNet is ruled out for the same reason it's ruled out everywhere else in this portfolio  it carries forward exactly the kind of undifferentiated network boundary that made PCI scope as broad as it is today (`current-state.md` §3), and gives Checkout & Payment's isolated network segment (ADR-005) nothing real to be isolated from. Three independent hub-and-spokes, manually peered, is what Case Study 3 chose  but Case Study 3 only needed two regions to talk to each other some of the time (during an active failover). This design needs three regions talking to a shared resource *continuously*: every region's Storefront & Catalog reads from its local Global Catalog replica, but that replica is fed by ongoing replication from the US primary (ADR-007), and Order Orchestration's saga compute (ADR-008) may need to reach shared platform services regardless of region. Manual VNet peering doesn't transit  a EU-to-APAC peering would need its own separate connection alongside EU-to-US and APAC-to-US, an every-pair-connected mesh that grows combinatorially as more regions are added, the same non-transitivity problem Case Study 3's GCP track (ADR-021 there) hit with plain VPC Peering, arrived at independently here for the equivalent reason on Azure's own peering primitive. Virtual WAN's regional hubs are automatically interconnected over Microsoft's own global backbone  any-to-any regional connectivity without a peering mesh to build and maintain  which is the direct structural fit for a genuinely three-region-active topology, not three two-region topologies bolted together.

**Trade-off:**
Virtual WAN is a higher-abstraction, more managed (and typically more expensive) product than self-assembled hub-and-spoke VNet peering  Solstice trades some fine-grained control over the exact routing and NVA placement for Microsoft operating the backbone connectivity. Accepted because the alternative  a three-way peering mesh maintained by a 22-person engineering org already carrying the compute/database/messaging surface area from ADR-005 through ADR-009  is real, avoidable operational load for a team ADR-002 already committed to keeping lean. Each regional hub still needs its own Azure Firewall for egress control and threat-intelligence filtering (Virtual WAN's Secured Virtual Hub pattern), so this decision doesn't reduce security posture relative to hub-and-spoke, only the peering-mesh maintenance burden.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Topology | Azure Virtual WAN, Standard tier |
| Regional hubs | US, EU, APAC  one Secured Virtual Hub per region, each with an integrated Azure Firewall |
| Spoke per region | One spoke VNet, subnets for: Storefront & Catalog/Cart Container Apps environment (ADR-005), Checkout & Payment Container Apps environment (ADR-005), Order Orchestration Container Apps environment (ADR-008), database private endpoints (ADR-006/ADR-007), Front Door/APIM private-link connectivity (ADR-012) |
| Inter-hub connectivity | Automatic, over Microsoft's global backbone  no manual peering |
| Egress control | Forced tunneling through each regional hub's Azure Firewall; no direct-to-internet path from any spoke subnet |
| Cross-region traffic in practice | Global Catalog replication (US primary → EU/APAC replicas, ADR-007) is the only steady-state cross-region data path; Cart/Checkout/Orders/Event Bus traffic (ADR-006, ADR-009) stays entirely within its own region by design |

**Status:** Approved

---

See [`../diagrams/azure-network-topology.png`](../diagrams/azure-network-topology.png) for the detailed diagram matching this ADR's Decision  the three Secured Virtual Hubs (US, EU, APAC) connected automatically over Microsoft's backbone, each region's spoke VNet and its contents (ADR-005, ADR-006/ADR-007, ADR-008, ADR-012), and the full Proposed Configuration table. Checked against this ADR and its dependencies before being finalized.
