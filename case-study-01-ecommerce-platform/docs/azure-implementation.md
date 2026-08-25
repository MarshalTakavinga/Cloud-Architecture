# Azure Implementation — Solstice Retail Group

This document implements the vendor-neutral logical design (Step 5) once on Microsoft Azure. It is one of three parallel implementations (Azure, AWS, GCP — no private-cloud track, per this case study's Scope Note) that will be scored against each other in a weighted decision matrix in Step 9 — nothing here is the final platform choice. Building it thoroughly rather than sketching it is what makes a fair comparison possible, matching the rigor Case Study 3 applied at this stage.

This document covers the platform as a whole — service selection, networking, security, observability, IaC. For a deeper, per-service treatment of exactly how each owned service is hosted, connects to its data, is reached, and scales, see [`application-architecture.md`](application-architecture.md).

## 1. Service Mapping

| Logical Component | Azure Service | Tier / Notes | Why |
| --- | --- | --- | --- |
| CDN / Edge | Azure Front Door | Premium tier, global | Closes the "no CDN in front of static assets" gap named in `current-state.md` §1 (see ADR-012) |
| API Gateway | Azure API Management | Premium tier, one instance per active region | Single ingress, token validation, per-region to avoid a global-instance bottleneck (see ADR-012) |
| Identity Provider | Microsoft Entra External ID | Dedicated customer tenant, separate from Solstice's workforce Entra ID | Purpose-built consumer CIAM, not a workforce directory repurposed for millions of retail customers (see ADR-010) |
| Storefront & Catalog Service | Azure Container Apps | Consumption + Dedicated mixed profile, one environment per active region | Fast, KEDA-driven elastic scaling for the 25x/5-minute requirement, no cluster to operate (see ADR-005) |
| Cart Service | Azure Container Apps | Same environment as Storefront & Catalog | Session-scoped, same scaling shape as Storefront & Catalog (see ADR-005) |
| Checkout & Payment Service | Azure Container Apps | **Separate, dedicated environment** per active region, own subnet | PCI isolation as a structural network property, not just a policy statement (see ADR-005) |
| Inventory & Order Orchestration Service | Azure Container Apps | Separate dedicated environment per active region, KEDA queue-length scaling | Saga-shaped workflow, different scaling trigger and blast radius than customer-facing traffic (see ADR-008) |
| Global Catalog Read Store | Azure Database for PostgreSQL Flexible Server (geo-replication) + Azure Cache for Redis (read-through accelerator) | US primary, EU/APAC read replicas | Same PostgreSQL engine as today, native geo-replication matches ADR-003's single-writer/multi-reader topology (see ADR-007) |
| Regional Transactional Store (×3) | Azure Database for PostgreSQL Flexible Server | General Purpose, zone-redundant, one independent server per region | Same engine, no schema conversion — `requirements.md` §4 doesn't call for a data-model rebuild (see ADR-006) |
| Event Bus | Azure Service Bus | Premium tier, one namespace per active region | Session-ordered, dead-lettered order events, scoped to Order Orchestration only per ADR-002 (see ADR-009) |
| Payment Gateway | Third-party, unchanged | External, PCI Level 1, hosted-fields tokenization | Unchanged from current state (`current-state.md` §5); Azure's only role is *not* being in this data path (ADR-004) |
| Session / catalog cache | Azure Cache for Redis | Standard tier, one instance per active region | Direct managed replacement for the self-managed Redis named in `current-state.md` §1 — session state (Cart) and read-through catalog cache (Storefront & Catalog) |
| Product search | Azure AI Search | Standard tier, one index per active region, fed from the regional catalog read replica | Managed replacement for the self-managed 3-node Elasticsearch cluster named in `current-state.md` §1 |
| Secrets Manager | Azure Key Vault | Standard tier, RBAC-enabled | Every service authenticates against this via managed identity instead of embedded secrets |
| Observability | Azure Monitor + Application Insights + Log Analytics (one workspace per region) | — | Closes the "no distributed tracing, no business-level signals" gap named in `current-state.md` §4 |
| Network | Azure Virtual WAN | Regional hub per active region, Secured Virtual Hub with Azure Firewall | Genuine any-to-any multi-region connectivity without a manual peering mesh (see ADR-011) |
| Fulfillment / Warehouse | Existing system, unchanged | Out of scope | `problem-statement.md` §5 — this design only produces the `OrderPlaced` event it already consumes |

## 2. Compute — Customer-Facing Regional Services (see ADR-005)

Storefront & Catalog, Cart, and Checkout & Payment all run on Azure Container Apps, chosen specifically because its KEDA-based scaling can react to the 20–25x, single-digit-minute traffic ramps `requirements.md` §1 documents as having actually happened, without handing Solstice's 22-person engineering org a Kubernetes cluster to operate. Storefront & Catalog and Cart share one Container Apps Environment per active region; Checkout & Payment gets its own, separate environment per region, injected into its own dedicated subnet — the structural implementation of the "isolated network segment" ADR-001 and ADR-002 already decided Checkout & Payment needs. See ADR-005's Proposed Configuration for replica counts and scale-rule detail, and [`application-architecture.md` §1–§3](application-architecture.md) for how each service actually reaches its data.

## 3. Compute — Inventory & Order Orchestration (see ADR-008)

Order Orchestration's saga (reserve inventory → confirm payment → create order → hand off to fulfillment) runs on its own dedicated Container Apps environment per region, scaled on Service Bus queue-length via KEDA rather than HTTP concurrency — a genuinely different load signal than the customer-facing tier, which is why it isn't sharing an environment with Storefront & Catalog/Cart. See ADR-008 and [`application-architecture.md` §4](application-architecture.md).

## 4. Database — Regional Transactional Store (see ADR-006)

Cart, Checkout, and Order data stays on the same PostgreSQL engine it runs on today — Azure Database for PostgreSQL Flexible Server, one independent, zone-redundant server per active region, with no cross-region replication between them, directly implementing ADR-003's regional-primary partitioning. This was chosen deliberately over Azure SQL Database/Managed Instance (which would mean a database-engine migration nothing in this case study's scope calls for) — see ADR-006 for the full reasoning and Proposed Configuration.

## 5. Database — Global Catalog (see ADR-007)

The catalog uses the same PostgreSQL engine, but a different topology: a single-writer primary in the US region with asynchronous, read-only geo-replicas in EU and APAC, directly implementing ADR-003's single-writer/multi-region-read pattern. Azure Cache for Redis sits in front of each region's replica as a read-through accelerator for the highest-traffic product pages — a cache, not the replication mechanism itself. See ADR-007.

## 6. Networking

- **Regional hubs**: Azure Virtual WAN with a Secured Virtual Hub (integrated Azure Firewall) in each of US, EU, and APAC — chosen over three independently-peered hub-and-spokes specifically because this design needs genuine any-to-any regional connectivity (continuous catalog replication traffic, ADR-007), not the occasional-failover connectivity Case Study 3's two-region hub-and-spoke was built for. See ADR-011.
- **Regional spokes**: one spoke VNet per region, with dedicated subnets for the Storefront & Catalog/Cart Container Apps environment, the Checkout & Payment Container Apps environment, the Order Orchestration Container Apps environment, database private endpoints, and API Management's VNet injection.
- **Egress control**: every spoke forces default-route egress through its regional hub's Azure Firewall — no direct-to-internet path from any subnet, the same Zero Trust posture Case Study 3 applied, arrived at independently here because the underlying reasoning (don't trust the network by default) doesn't change with the workload.

### 6.1 Network Addressing Plan

Non-overlapping ranges across all three regions up front, since Virtual WAN's hub connectivity means any region can, in principle, reach any other without a later re-addressing exercise.

| Region | VNet | Subnet | Range | Purpose |
| --- | --- | --- | --- | --- |
| US | 10.10.0.0/16 | snet-storefront-cart | 10.10.1.0/24 | Storefront & Catalog / Cart Container Apps environment (ADR-005) |
| | | snet-checkout | 10.10.2.0/24 | Checkout & Payment Container Apps environment — PCI-isolated (ADR-005) |
| | | snet-orchestration | 10.10.3.0/24 | Order Orchestration Container Apps environment (ADR-008) |
| | | snet-db-pe | 10.10.4.0/24 | Regional Transactional Store + Global Catalog replica private endpoints (ADR-006, ADR-007) |
| | | snet-apim | 10.10.5.0/24 | API Management VNet injection (ADR-012) |
| EU | 10.20.0.0/16 | snet-storefront-cart | 10.20.1.0/24 | Same pattern as US |
| | | snet-checkout | 10.20.2.0/24 | |
| | | snet-orchestration | 10.20.3.0/24 | |
| | | snet-db-pe | 10.20.4.0/24 | Holds the EU Global Catalog **read replica** (ADR-007), not a writable primary |
| | | snet-apim | 10.20.5.0/24 | |
| APAC | 10.30.0.0/16 | snet-storefront-cart | 10.30.1.0/24 | Same pattern as US |
| | | snet-checkout | 10.30.2.0/24 | |
| | | snet-orchestration | 10.30.3.0/24 | |
| | | snet-db-pe | 10.30.4.0/24 | Holds the APAC Global Catalog **read replica** (ADR-007) |
| | | snet-apim | 10.30.5.0/24 | |

`snet-checkout` in every region carries its own network security group, allow-listing only the specific traffic Checkout & Payment actually needs (inbound from `snet-apim`, outbound to `snet-db-pe` and the external Payment Gateway) and denying everything else, including traffic from `snet-storefront-cart` in the same region — the concrete enforcement behind ADR-005's "isolated network segment."

## 7. Global Entry — CDN/Edge and API Gateway (see ADR-012)

Azure Front Door Premium is the single global entry point: latency-based routing to the nearest healthy active region, static-asset caching, and a managed WAF ruleset — the direct fix for `current-state.md` §1's "no CDN in front of static assets" gap. Behind it, each region runs its own Azure API Management Premium instance, validating Entra External ID tokens (Section 8) and applying rate-limiting policy before any request reaches Storefront & Catalog, Cart, or Checkout & Payment. See ADR-012.

## 8. Identity and Security

- Microsoft Entra External ID issues OAuth2/OIDC tokens for customer sign-in, validated at each region's API Management instance — a dedicated consumer tenant, deliberately separate from Solstice's workforce Entra ID, the same population-separation discipline Case Study 3 applied between patient and workforce identity (see ADR-010).
- Every PaaS service (API Management, Container Apps, PostgreSQL Flexible Server, Service Bus, Redis) is reached through a private endpoint inside its regional spoke, never the public internet.
- Azure Key Vault holds every credential and certificate; managed identities let Container Apps, API Management, and other components authenticate without embedded secrets.
- Checkout & Payment's own Container Apps environment and subnet (Section 6) is the structural PCI isolation boundary — cardholder data never reaches it anyway, since ADR-004's client-side hosted fields send it straight from the customer's browser to the Payment Gateway, but the isolated boundary still narrows blast radius for everything else that *does* run there (order-capture logic, the payment token itself).
- Microsoft Defender for Cloud provides workload-level threat detection across the Container Apps, database, and cache layers.

## 9. Messaging — Azure Service Bus

Order events (`order-placed`, `inventory-reserved`, `payment-confirmed`, `order-confirmed`, `order-cancelled`, `inventory-released`) route through session-enabled Service Bus topics, one independent Premium namespace per active region — matching the regional-primary shape of the orders that produce them (ADR-003) rather than one global namespace. Built-in dead-lettering means a failed or unprocessable order event doesn't silently disappear. See ADR-009 and [`application-architecture.md` §4](application-architecture.md).

## 10. Observability

Every service ships logs, metrics, and distributed traces to a regional Log Analytics workspace via Azure Monitor and Application Insights — directly closing the two gaps `current-state.md` §4 named: no distributed tracing across service boundaries, and no business-level signals (checkout success rate, cart-to-order conversion latency) alongside the infrastructure metrics that already existed. Alerts are tied to the signals that actually matter operationally: Service Bus dead-letter queue depth, PostgreSQL replication lag on the Global Catalog replicas, Container Apps replica count approaching its configured ceiling during a named peak event (an early warning that the ceiling itself may need raising before the event, not during it).

## 11. Regional-Outage Response

This is deliberately not framed as a "disaster recovery" section the way Case Study 3's was — Case Study 3's DR design exists to fail an entire application over from one primary region to a warm standby. This design has no primary region; all three are active all the time, for latency, not failover (`architecture-options-and-styles.md` §3). A regional outage here doesn't trigger a failover — it means one region is temporarily unreachable while the other two continue serving their own customers unaffected, and Front Door's health probes simply stop routing new traffic to the unhealthy region.

| Scenario | What happens | What doesn't |
| --- | --- | --- |
| One region's Storefront & Catalog/Cart/Checkout compute becomes unhealthy | Front Door's health probes detect it and stop routing new customer traffic there; the other two regions are unaffected | No cross-region compute failover — a customer normally served by the down region gets routed to the next-nearest healthy region instead, at a latency cost `requirements.md` §3's targets don't cover for that window, an accepted, named trade-off |
| One region's Regional Transactional Store becomes unavailable | Customers whose home region that is lose write availability for in-flight carts/orders until it recovers (ADR-003's already-accepted trade-off, ADR-006 implements it) | No automatic cross-region write failover — building one would mean abandoning regional-primary partitioning or building active-active multi-master for financial data, both rejected in ADR-003 |
| The US region (Global Catalog primary) becomes unavailable | EU and APAC continue serving their local read replicas — catalog *reads* are unaffected; catalog *writes* (merchandising/back-office) are blocked until an operator manually promotes a replica (ADR-007) | No automatic replica promotion — a deliberate choice to avoid a split-brain write scenario over a catalog-write outage that doesn't stop customers from browsing or completing an in-flight cart |

## 12. Infrastructure as Code

Bicep is the primary IaC tool — Azure-native, first-class support for Container Apps, Virtual WAN, and every other resource type used above. Terraform is reserved for the cross-platform comparison work in the decision-matrix stage (Step 9), the same split Case Study 3 used, for the same reason: one tool spanning all three candidate platforms matters more at that stage than native fluency on any single one.

## 13. Alignment Check

A gut-check against Microsoft's Azure Well-Architected pillars before moving on:

| Pillar | How this design addresses it |
| --- | --- |
| Reliability | Zone-redundant compute and database per region, three genuinely independent active regions (not one primary + standby), Service Bus dead-lettering |
| Security | Zero Trust via Entra token validation + private endpoints everywhere, Key Vault-managed secrets, a structurally isolated PCI network segment for Checkout & Payment |
| Cost Optimization | Deferred to the cost/risk analysis stage (Step 13) — sizing above is directional, not final; Consumption-plus-Dedicated Container Apps profiles are chosen specifically to avoid paying peak-capacity prices year-round, the direct answer to `requirements.md` §3's 30%-cost-reduction target |
| Operational Excellence | Bicep IaC, centralized per-region observability, a network topology (Virtual WAN) chosen specifically to reduce peering-mesh maintenance for a lean engineering org |
| Performance Efficiency | KEDA-driven Container Apps scaling reacts inside the 5-minute elasticity target; Front Door + regional APIM keeps API-policy enforcement close to the services it protects instead of round-tripping to one global instance |

## 14. Explicitly Deferred

- Exact compute/database sizing and cost modeling — Step 13
- Final platform recommendation — Step 9, after AWS and GCP implementations exist to compare against
- Detailed IAM role/permission definitions
- Bicep modules themselves (built once, during the migration roadmap stage, for whichever platform is chosen)
- Remaining decision-specific diagrams for this step (mirroring Step 5's per-ADR detail diagrams) — the overview diagram, the ADR-006 detail diagram, and the ADR-007 detail diagram are now in §15; a corrected ADR-005 detail diagram is still pending (see note below), and the rest can follow the same pattern if needed

## 15. Diagrams

[Azure implementation architecture diagram](../diagrams/azure-implementation-architecture.png) — full-stack view of this document: global entry (Front Door), per-region API Management, Entra External ID, the three active regions' compute/data/integration/network layers, the Global Catalog single-writer topology (ADR-007), and Virtual WAN connectivity (ADR-011). Checked against this document and ADR-005 through ADR-012.

[ADR-006 detail diagram](../diagrams/adr-006-database-service.png) — see the reference and review notes at the bottom of `ADR-006-azure-database-regional-transactional-store.md`.

[ADR-007 detail diagram](../diagrams/adr-007-database-service.png) — see the reference and review notes at the bottom of `ADR-007-azure-database-global-catalog.md`.

An ADR-005 detail diagram (compute hosting for the customer-facing services) was drafted but not added here — across multiple review rounds its "Outbound to Payment Gateway" arrows never reached a fully independent per-region topology (one region's PCI Isolated Subnet kept arrowing into another region's Checkout & Payment Service box instead of to the external gateway). Not included pending a corrected version.
