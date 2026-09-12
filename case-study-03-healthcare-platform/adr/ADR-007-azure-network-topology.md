### ADR-007: Azure network topology

**Context:**
The logical design carries forward Meridian's existing hub-and-spoke mental model. Azure offers two realistic ways to implement that shape: a traditional hub VNet with peered spoke VNets, or Azure Virtual WAN, a managed hub service aimed at large-scale, many-site connectivity.

**Options considered:**
- Traditional hub-and-spoke: a hub VNet (firewall, gateway, shared services) peered to application and data spoke VNets
- Azure Virtual WAN: a Microsoft-managed hub that automates peering, routing, and branch connectivity at scale

**Decision:** Traditional hub-and-spoke with VNet peering.

**Rationale:**
Virtual WAN earns its cost and complexity at a scale this workload doesn't have yet — many regions, many branch sites connecting directly into the cloud network, or a need for Microsoft-managed routing across dozens of VNets. Meridian's Azure footprint for this case study is a primary region and one paired DR region, with clinics still connecting via existing site-to-site links during migration. A traditional hub-and-spoke gives full control over the firewall and routing configuration at a lower cost, and is the more common, better-understood pattern for a workload at this scale.

**Trade-off:**
If Meridian's Azure footprint grows substantially — many more regions, or clinics connecting directly to Azure instead of through a central hub — traditional hub-and-spoke becomes harder to manage than Virtual WAN would have been. That re-evaluation point is named explicitly rather than assumed never to happen: if the number of spokes or regions grows past what one team can manage by hand, revisit this decision.

**Status:** Proposed
