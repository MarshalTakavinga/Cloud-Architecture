# ADR-011: Azure Network Connectivity, Identity, and Pull-Based Edge Deployment

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 4 pipeline

## Context

[ADR-003](ADR-003-ot-segmentation-reference-architecture.md) sets these rules:
- Level 3 has no direct route out
- all traffic crossing the plant boundary passes through the DMZ
- connections to the cloud are outbound only
- models and configuration are **pulled** by the plant and never pushed in

Step 5 requires signed artifacts, shadow-mode activation with plant approval, and one-step rollback. Traffic volumes are small, about 1–5 Mbps per plant or about 60 Mbps in aggregate steady state. The US and Mexico plants already reach the internet through Columbus over MPLS. The German plants use local internet.

Microsoft's current guidance for IoT Operations in layered, Purdue-style networks is **Envoy proxy chaining** between layers, with the **Azure Arc gateway** (which consolidates the Azure endpoints that must be allowed) or an explicit firewall proxy, and Private Link for data destinations. **ACR connected registry** can run on-premises as an Arc extension in `ReadOnly` mode and sync a subset of repositories from the cloud registry.

## Decision

**Network path**
- **In the plant DMZ:** an **Envoy explicit proxy** is the only egress for the Level 3 cluster, with an allowlist of the Arc gateway endpoint plus the private-endpoint FQDNs for Event Hubs and ACR. The DMZ firewall permits the Level 3 cluster to reach the proxy and nothing else outbound.
- **US and Mexico plants to Azure:** existing MPLS to Columbus, then an **active-active site-to-site VPN** (two tunnels) from Columbus to the US hub VNet. SAP ECC is reached over the same VPN in the other direction.
- **German plants to Azure:** a **site-to-site VPN from each plant** to the EU hub VNet in Germany West Central. EU traffic never transits Columbus.
- **PaaS services** (Event Hubs, SQL, ACR, Azure ML, Fabric through managed private endpoints) are reached only through private endpoints in the hub-and-spoke landing zone. Azure Policy denies public network access.

**Identity**
- **Human access:** Entra ID. Plant engineers get just-in-time, MFA-enforced roles. The OT secure-remote-access product from ADR-003 is separate from, and does not rely on, cloud identity.
- **Workload access:** plant workloads authenticate to Azure through **Arc-enabled workload identity federation**, so no secrets are stored at the plant. Plant-local mTLS for the MQTT broker and PostgreSQL uses a plant-local CA, so local operation never depends on Azure (see [ADR-006](ADR-006-azure-edge-platform.md)).

**Pull-based deployment (P9)**
- **Configuration:** configuration and workload manifests live in Git. **Arc GitOps (Flux)** on each cluster *pulls* them through the proxy.
- **Images and model artifacts:** these are built into **Azure Container Registry** and signed with Notation. Each plant's **ACR connected registry (`ReadOnly`) in the DMZ** syncs only the repositories that plant needs. Clusters pull from it, and admission policy rejects any unsigned image.
- **Model activation:** a Kestrel-built activation controller deploys each new model version in **shadow mode**. It promotes the model to active only after a plant reliability engineer approves it, recorded as a signed Git commit in that plant's environment branch and logged to the audit table. Rollback is a Git revert, and the previous image stays cached in the connected registry.
- **Rollout:** plant by plant, through GitOps environment branches (pilot plant, then waves).

## Alternatives Considered (rejected, retained here rather than deleted)

1. **ExpressRoute from Columbus (and a second circuit for the EU).** Rejected as disproportionate. Steady-state volume is about 60 Mbps, and nothing on the production-critical path depends on the WAN ([ADR-001](ADR-001-edge-cloud-responsibility-split.md)). A redundant VPN gives enough reliability at a fraction of the cost. This contrasts deliberately with Case Study 2, where the mainframe hold path made private, predictable latency a regulatory need. It can be revisited if SAP moves to Azure as part of the S/4HANA program.
2. **Plant clusters connecting directly to Azure endpoints over the internet, with no DMZ proxy.** Rejected. It violates ADR-003: Level 3 would have a direct outbound route, and there would be no single inspection and allowlist point per plant.
3. **Push-based deployment from a cloud pipeline into the clusters.** Rejected. It requires inbound reachability to plant clusters, which is forbidden by ADR-003, and it removes the plant's approval gate from the path.

## Consequences

- **Positive:** Every ADR-003 rule is implemented with supported Microsoft components (the Arc gateway, the documented Envoy pattern, ACR connected registry, Flux). The plant's attack surface toward the cloud is one proxy with an explicit allowlist.
- **Positive:** Deployments are auditable end to end. What a plant runs is exactly what its Git branch says, signed and approved.
- **Negative / accepted trade-off:** Each plant DMZ now hosts three platform services (the proxy, the Arc gateway client configuration, and the connected registry). That is more DMZ infrastructure to patch in plants without IT staff, so it is included in the managed-operations scope in Step 12.
- **Negative / accepted trade-off:** Plant-local CAs for mTLS add a certificate lifecycle to manage, 12 times over. They are centrally monitored, but they are a deliberate trade for WAN-independent local operation.
