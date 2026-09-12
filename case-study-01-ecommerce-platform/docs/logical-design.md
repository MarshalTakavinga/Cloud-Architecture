# Vendor-Neutral Logical Design  Solstice Retail Group

Step 5 turns Step 4's style decision into an actual system: named components, real data flow, and the two decisions that were still open  how data is actually distributed across regions, and exactly how card data avoids Solstice's servers. No cloud platform is chosen here  every component below is named by capability, not by product, so Steps 6–8 can evaluate Azure, AWS, and GCP fairly against the same design, the same discipline Case Study 3 applied at this stage.

## 1. What This Step Adds

ADR-001 and ADR-002 named four owned components and a target style. This step adds what was implied but not yet drawn: a CDN/edge layer that didn't exist at all in the current state (the direct fix for the ~2.1s EU page-load gap), an Identity Provider for customer sign-in and session, an API Gateway as the single ingress point across all four services, an Event Bus (already implied by ADR-002's scoped event-driven adoption), and  cross-cutting, not owned by any one service  an observability platform, closing the "no distributed tracing, no business-level signals" gap named in `current-state.md` §4.

## 2. Components

| Component | Role | Traces to |
| --- | --- | --- |
| CDN / Edge | Latency-based routing to the nearest live region; caches static assets and cacheable storefront responses | Closes the "no CDN at all" gap, `current-state.md` §1 |
| API Gateway | Single ingress for all customer-facing traffic; the seam that lets four components move at different speeds without looking like four broken systems | Same role APIM/API Gateway/Apigee played in Case Study 3 |
| Identity Provider | Customer sign-in, session issuance | New  current state has no dedicated identity component; folded into the monolith today |
| Storefront & Catalog Service | Browse, search, product pages  stateless, horizontally scalable | ADR-001 (Rearchitect) |
| Global Catalog Read Store | Product/catalog data, replicated for local reads in every active region | ADR-003 |
| Cart Service | Session-scoped cart state | ADR-001 (Refactor) |
| Checkout & Payment Service | Order capture and payment initiation, isolated network segment | ADR-001 (Rearchitect), ADR-004 |
| Payment Gateway | Third-party, PCI Level 1, hosted tokenization | External  unchanged from current state (`current-state.md` §5) |
| Inventory & Order Orchestration Service | Order placement → inventory reservation → payment confirmation → fulfillment handoff | ADR-001 (Rearchitect) |
| Regional Transactional Store (×3: US, EU, APAC) | Cart, checkout, and order data  regional-primary, relational, same schema as today | ADR-003; `requirements.md` §4 (schema not being redesigned) |
| Event Bus | Asynchronous, replayable order events | ADR-002 |
| Observability Platform | Distributed tracing + business-level signals (checkout success rate, cart-to-order latency), not just infrastructure metrics | Closes `current-state.md` §4's named gap |
| Fulfillment / Warehouse | Existing system, receives the order-placed event | Out of scope  `problem-statement.md` §5 |

## 3. ADR-003  Multi-Region Data Topology

`architecture-options-and-styles.md` §3 already decided active-active reads for the storefront and regional-primary writes for cart/checkout/orders, at the level of a style choice. This step makes it concrete enough to actually build against  see [ADR-003](../adr/ADR-003-multi-region-data-topology.md). Two genuinely different data patterns, not one:

- **Catalog: single-writer, multi-region read replicas.** Product and price data changes relatively infrequently compared to storefront read volume, and comes from one place (merchandising/back-office), so a single write path with asynchronously-replicated read copies in every active region is the right-sized pattern  not a rewrite of the relational schema `requirements.md` §4 already ruled out touching, just a different deployment topology for it.
- **Cart, checkout, and orders: regional-primary partitioning.** Each active region (US, EU, APAC) has its own primary datastore for these three  a US customer's cart writes land in the US primary, an EU customer's in the EU primary. This is what actually satisfies the GDPR residency requirement structurally, and it's a genuinely different pattern from the catalog's single-writer model, which is exactly why Case Study 3's "one database for everything" assumption doesn't transfer here.

## 4. ADR-004  Payment Tokenization Approach

`current-state.md` §3 traced the PCI finding precisely: cardholder data transits Solstice's application tier before the gateway tokenizes it. ADR-002 named the fix in principle (hosted tokenization); [ADR-004](../adr/ADR-004-payment-tokenization-approach.md) makes the specific mechanism concrete  client-side hosted fields, not a server-side API call carrying raw card data. This is the one decision in this step that isn't platform-neutral in the usual sense: it's a payment-gateway-capability decision, not a cloud-platform decision, which is why it's made once here rather than three times in Steps 6–8.

## 5. Reading the Logical Architecture Diagram

Every element in [`diagrams/logical-architecture.png`](../diagrams/logical-architecture.png) traces to a decision above, not an aesthetic choice:

- Three region markers (US, EU, APAC) around the Storefront & Catalog Service and the Global Catalog Read Store show the single-writer/multi-reader pattern from ADR-003  one write arrow in, replication fanning out to all three.
- Three separate Regional Transactional Store boxes, each paired with its own region's Cart, Checkout & Payment, and Order Orchestration instances, show the regional-primary partitioning from ADR-003  there is deliberately no arrow connecting the three regional stores to each other.
- The dashed line from Customers directly to the Payment Gateway, bypassing the Checkout & Payment Service entirely, is ADR-004's hosted-tokenization mechanism drawn as data flow, not just described in prose.
- The Observability Platform is drawn cross-cutting, attached to every component with a dotted line, the same convention Case Study 3 used for its cross-cutting Identity/Secrets/Logging components at this same step.
