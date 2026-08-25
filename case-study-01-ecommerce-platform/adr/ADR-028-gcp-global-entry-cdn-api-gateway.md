### ADR-028: GCP global entry point  CDN/Edge and API Gateway

**Context:**
`logical-design.md` §1 named two components together: a CDN/Edge layer that didn't exist at all in the current state  the direct fix for the ~2.1s EU page-load gap (`requirements.md` §3)  and an API Gateway as the single ingress point across all four owned services. Both sit in front of every region (ADR-027) and every customer-facing service (ADR-021), so this ADR decides the GCP services for the actual front door of the whole system.

**Options considered:**
- Cloud CDN + Global External Application Load Balancer alone for the edge layer, with no dedicated API Gateway product.
- A single combined layer, relying on the load balancer's own routing and Cloud Armor rules instead of adding an API Gateway as a second layer.
- Cloud CDN + Global External Application Load Balancer for the edge layer, paired with Google Cloud API Gateway (regional instances) for the API Gateway layer.

**Decision:**
Google Cloud CDN, layered on a Global External Application Load Balancer, as the global edge  a single global anycast IP, latency-based routing to the nearest healthy regional backend, static-asset caching, and Cloud Armor for WAF/DDoS protection  with Google Cloud API Gateway (one regional instance per active region, reached as a backend behind the load balancer) as the API Gateway layer, validating Identity Platform-issued OIDC tokens, applying quota and rate-limiting policies, and routing to each region's Cloud Run services (ADR-021) over Serverless VPC Access private connectivity.

**Rationale:**
CDN-and-load-balancer-only is rejected because it under-serves half of the actual requirement, the same gap ADR-012 and ADR-020 named on the other two tracks: caching and latency-based routing solve the static-asset and routing half of `logical-design.md`'s CDN/Edge component, but do nothing for the API Gateway's job  validating Identity Platform tokens, applying rate limiting per customer, and giving Storefront & Catalog, Cart, and Checkout & Payment a single, consistent ingress contract instead of three services each handling auth and routing themselves. A single combined layer is rejected because the load balancer's routing and Cloud Armor policies operate at the HTTP/edge layer and don't provide the token-validation, per-API-product rate-limiting, and backend-abstraction capabilities Solstice needs at the application layer  the same split-of-concerns reasoning ADR-012 and ADR-020 applied choosing two separate products on their own platforms. Cloud CDN plus regional Cloud API Gateway, deployed per active region, is the direct combination: worth naming the structural nuance rather than treating it as identical to CloudFront-in-front-of-API-Gateway  on GCP, the Global External Application Load Balancer is itself the single global resource carrying one anycast IP, with Cloud CDN as a caching mode layered onto it and Cloud Armor built directly into the load balancer, rather than two independently-provisioned edge products glued together at the origin level. Each region's Cloud API Gateway instance still does the actual token validation and API-level policy enforcement close to the Cloud Run services it routes to, rather than adding a round-trip back to one global instance for every request  Google Cloud API Gateway, like AWS API Gateway and Azure API Management, is itself a regional-only product with no multi-region or global variant, so per-region deployment is required regardless of the edge layer's own global nature.

**Trade-off:**
Two products in front of every request (the load balancer/CDN, then regional API Gateway) is one more hop, and one more thing to operate and monitor, than a single combined layer  accepted for the identical reason ADR-012 and ADR-020 accepted it on the other tracks: the two products solve genuinely different problems, and collapsing them would mean one taking on responsibilities it isn't built for. Per-region API Gateway deployments (rather than one global instance) mean per-region configuration to keep in sync across three regions, the same operational discipline ADR-020's per-region API Gateway required.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Edge | Cloud CDN, layered on a Global External Application Load Balancer |
| WAF / DDoS | Cloud Armor (managed rule sets, OWASP-equivalent coverage), built into the load balancer |
| Routing | Latency-based, single global anycast IP routes to the nearest healthy regional backend |
| Caching | Static assets and cacheable storefront responses, per `logical-design.md`'s CDN/Edge role |
| API Gateway | Google Cloud API Gateway, one regional instance per active region |
| Token validation | Identity Platform-issued OIDC tokens validated at the gateway (ADR-026), before any request reaches Storefront & Catalog, Cart, or Checkout & Payment |
| Rate limiting | API Gateway quota and rate-limit policies, configured identically across all three regional deployments |
| Backend routing | API Gateway routes to the correct Cloud Run service (ADR-021) based on resource path  storefront/catalog reads, cart operations, checkout initiation  over Serverless VPC Access private connectivity, not the public internet |

**Status:** Approved
