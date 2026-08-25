### ADR-020: AWS global entry point — CDN/Edge and API Gateway

**Context:**
`logical-design.md` §1 named two components together: a CDN/Edge layer that didn't exist at all in the current state — the direct fix for the ~2.1s EU page-load gap (`requirements.md` §3) — and an API Gateway as the single ingress point across all four owned services. Both sit in front of every region (ADR-019) and every customer-facing service (ADR-013), so this ADR decides the AWS services for the actual front door of the whole system.

**Options considered:**
- Amazon CloudFront (global CDN, WAF, DDoS absorption) for the edge layer, paired with Amazon API Gateway for the API Gateway layer.
- Amazon CloudFront alone for static-asset caching, with regional Application Load Balancers handling routing and no dedicated API Gateway product.
- A single combined layer, relying on CloudFront's own routing and WAF rules instead of adding API Gateway as a second layer.

**Decision:**
Amazon CloudFront as the global edge — latency/geo-based routing to the nearest healthy active region, static-asset caching, and AWS WAF — with Amazon API Gateway (REST API, regional endpoint type, one instance per active region, behind CloudFront) as the API Gateway layer, using a Cognito User Pool authorizer for token validation, usage plans for rate limiting, and VPC Link integration routing to each region's ECS Fargate services over private connectivity.

**Rationale:**
CDN-only with regional Application Load Balancers is rejected because it under-serves half of the actual requirement, the same gap ADR-012 named on Azure: caching and edge routing solve the static-asset and latency-based-routing half of `logical-design.md`'s CDN/Edge component, but do nothing for the API Gateway's job — validating the Cognito tokens from ADR-018, applying rate limiting per customer, and giving Storefront & Catalog, Cart, and Checkout & Payment a single, consistent ingress contract instead of three services each handling auth and routing themselves. A single combined layer is rejected because CloudFront's routing and WAF policies operate at the HTTP/edge layer and don't provide the token-validation, per-API-product rate-limiting, and backend-abstraction capabilities Solstice needs at the application layer — the same split-of-concerns reasoning ADR-012 applied choosing Front Door plus API Management as separate products on Azure. CloudFront plus regional API Gateway, deployed per active region, is the direct combination: CloudFront does global latency/geo-based routing and absorbs the WAF/DDoS surface at the true network edge via AWS Shield Standard (automatically included with every CloudFront distribution — a genuine, small platform difference from Azure's separately-named DDoS Protection product, worth carrying into Step 9's comparison rather than treated as an identical line item), and each region's API Gateway instance does the actual token validation and API-level policy enforcement close to the ECS services it routes to via VPC Link, rather than adding a round-trip back to one global instance for every request.

**Trade-off:**
Two products in front of every request (CloudFront, then regional API Gateway) is one more hop, and one more thing to operate and monitor, than a single combined layer — accepted for the identical reason ADR-012 accepted it on Azure: the two products solve genuinely different problems, and collapsing them would mean one taking on responsibilities it isn't built for. Per-region API Gateway deployments (rather than one global instance) mean per-region configuration to keep in sync across three regions — accepted because a single global API Gateway would become exactly the kind of centralized bottleneck the multi-region active-active design (ADR-019) exists to avoid.

One configuration point worth naming explicitly rather than leaving implicit: Amazon API Gateway REST APIs support both an "edge-optimized" endpoint type (automatically fronted by a CloudFront distribution API Gateway manages itself) and a "regional" endpoint type. This design deliberately uses **regional** endpoints behind an explicitly-configured, separately-managed CloudFront distribution, not edge-optimized — so CloudFront's routing, caching, and WAF behavior is controlled directly by this design rather than by API Gateway's own default edge configuration, keeping the two layers' responsibilities as deliberately separated as ADR-012's Azure equivalent.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Edge | Amazon CloudFront |
| WAF / DDoS | AWS WAF (managed rule groups, OWASP-equivalent coverage) + AWS Shield Standard (automatic with CloudFront) |
| Routing | Latency/geo-based, routes to the nearest healthy regional API Gateway origin |
| Caching | Static assets and cacheable storefront responses, per `logical-design.md`'s CDN/Edge role |
| API Gateway | Amazon API Gateway, REST API, regional endpoint type, one instance per active region |
| Token validation | Cognito User Pool authorizer (ADR-018) validates OAuth2/OIDC JWTs at the gateway, before any request reaches Storefront & Catalog, Cart, or Checkout & Payment |
| Rate limiting | Usage plans with per-customer throttling, configured identically across all three regional API Gateway deployments |
| Backend routing | API Gateway VPC Link integration routes to the correct ECS Fargate service (ADR-013) based on resource path — storefront/catalog reads, cart operations, checkout initiation — over private connectivity via a Network Load Balancer, not the public internet |

**Status:** Approved
