### ADR-012: Azure global entry point — CDN/Edge and API Gateway

**Context:**
`logical-design.md` §1 named two components together: a CDN/Edge layer that didn't exist at all in the current state — the direct fix for the ~2.1s EU page-load gap (`requirements.md` §3) — and an API Gateway as the single ingress point across all four owned services. Both sit in front of every region (ADR-011) and every customer-facing service (ADR-005), so this ADR decides the Azure services for the actual front door of the whole system.

**Options considered:**
- Azure Front Door (global HTTP/S load balancing, CDN, and WAF) for the edge layer, paired with Azure API Management for the API Gateway layer.
- Azure Content Delivery Network alone for static-asset caching, with regional Application Gateways per region handling routing and no dedicated API Gateway product.
- A single combined product doing both jobs — relying on Front Door's own routing rules and rate-limiting instead of adding API Management as a second layer.

**Decision:**
Azure Front Door (Premium tier) as the global edge — latency-based routing to the nearest healthy active region, static-asset caching, and WAF — with Azure API Management (Premium tier, deployed per region behind Front Door) as the API Gateway layer handling authentication/authorization, rate limiting, and request routing to the correct backend service.

**Rationale:**
CDN-only with regional Application Gateways is rejected because it under-serves half of the actual requirement: caching and edge routing (what a CDN does) solves the static-asset and latency-based-routing half of `logical-design.md`'s CDN/Edge component, but does nothing for the API Gateway's job — validating the Entra External ID tokens from ADR-010, applying rate limiting per customer, and giving Storefront & Catalog, Cart, and Checkout & Payment a single, consistent ingress contract instead of three services each handling auth and routing themselves — Order Orchestration is deliberately excluded from this contract, since it has no HTTP ingress at all (ADR-008, ADR-009) and is reached only via the Event Bus, not this gateway. A single combined product handling both jobs is rejected because Front Door's routing and WAF policies operate at the HTTP/edge layer — they don't provide the token-validation, per-API-product rate-limiting, and backend-abstraction capabilities Solstice needs at the application layer, the same reason Case Study 3 kept its edge (Front Door, for the Portal) and its API Gateway (APIM, for external lab/imaging integrations) as separate products rather than one. Azure Front Door plus API Management, deployed per active region, is the direct combination: Front Door does global latency-based routing and absorbs the DDoS/WAF surface at the true network edge (closing the "no CDN in front of static assets" gap `current-state.md` §1 named directly), and each region's APIM instance does the actual token validation and API-level policy enforcement close to the services it's routing to, rather than adding a round-trip back to a single global APIM instance for every request.

**Trade-off:**
Two products in front of every request (Front Door, then regional APIM) is one more hop, and one more thing to operate and monitor, than a single combined layer would be. Accepted because the two products solve genuinely different problems — global edge routing/caching versus per-region API policy enforcement — and collapsing them would mean either Front Door taking on API-management responsibilities it isn't built for, or APIM taking on global edge/CDN responsibilities it isn't built for either. Per-region APIM Premium instances (rather than one global instance) also mean per-region minimum cost and configuration to maintain in sync across three regions — accepted because a single global APIM instance would become exactly the kind of centralized bottleneck the multi-region active-active design (ADR-011) exists to avoid, and configuration drift across three instances is a manageable, monitorable risk compared to that.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Edge | Azure Front Door, Premium tier |
| WAF | Managed ruleset (OWASP Core Rule Set) + Front Door's own bot-protection rules |
| Routing | Latency-based, routes to the nearest active region with a healthy origin (APIM) |
| Caching | Static assets and cacheable storefront responses, per `logical-design.md`'s CDN/Edge role |
| API Gateway | Azure API Management, Premium tier, one instance per active region, VNet-integrated into that region's spoke (ADR-011) |
| Token validation | Validates Entra External ID (ADR-010) OAuth2/OIDC tokens at the gateway, before any request reaches Storefront & Catalog, Cart, or Checkout & Payment |
| Rate limiting | Per-customer and per-API-product policies, configured identically across all three regional APIM instances |
| Backend routing | APIM routes to the correct Container Apps environment (ADR-005) based on path — storefront/catalog reads, cart operations, checkout initiation — over the private VNet connection, not the public internet |

**Status:** Approved

---

See [`../diagrams/azure-global-entry-cdn-api-gateway.png`](../diagrams/azure-global-entry-cdn-api-gateway.png) for the detailed diagram matching this ADR's Decision — the global edge layer (Front Door: routing, CDN caching, WAF, DDoS), the per-region API Management layer (token validation, rate limiting, routing, VNet-integrated per ADR-011), and the full Proposed Configuration table. Checked against this ADR's own Proposed Configuration and `application-architecture.md` before being finalized: an early draft of the diagram showed Order Orchestration (ADR-008) as a fourth backend service reached through APIM in every region, alongside Storefront & Catalog, Cart, and Checkout & Payment — removed, since Order Orchestration has no HTTP ingress and is never routed to by this gateway. That same error was also present in this ADR's own Rationale text (it listed Order Orchestration as one of "four services" under the gateway's ingress contract, contradicting the Proposed Configuration table two paragraphs below it) — corrected there too, in the same pass. A "Caching" row in the diagram's Proposed Configuration table was also mistyped twice during editing ("Couting," then "Cacting") before landing correctly.
