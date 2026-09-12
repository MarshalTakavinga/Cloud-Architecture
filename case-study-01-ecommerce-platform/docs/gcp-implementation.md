# GCP Implementation  Solstice Retail Group

This document implements the vendor-neutral logical design (Step 5) once on Google Cloud Platform. It is one of three parallel implementations (Azure, AWS, GCP  no private-cloud track, per this case study's Scope Note) that will be scored against each other in a weighted decision matrix in Step 9  nothing here is the final platform choice. Building it thoroughly rather than sketching it is what makes a fair comparison possible, matching the rigor Case Study 3 applied at this stage and matching this case study's own Steps 6 and 7.

Like the AWS track and unlike the Azure track, this document is kept as a single file rather than split into a platform doc plus a separate per-service `application-architecture.md`  GCP's service boundaries (Cloud Run services, Cloud Workflows definitions) map closely enough to the ADR-level detail that a second document would mostly repeat it.

One fact shapes this track differently than the AWS track and is worth stating up front: **Solstice does not run on GCP today.** `current-state.md` §1 names the current production stack as AWS-native (EC2, RDS for PostgreSQL, self-managed Redis and Elasticsearch, S3). Unlike Step 7's AWS track, this GCP track carries no in-place migration familiarity or US-region cutover risk  every region, including US, provisions cleanly from a greenfield state (ADR-021). That is a genuine, honestly-stated simplification for this track's migration-planning story, worth carrying into Step 9's comparison rather than treated as a wash against AWS's operational-familiarity advantage.

Two genuinely GCP-native platform differences run through this document and are worth reading with attention rather than treated as implementation trivia: Google Cloud VPC networks are **global** resources (ADR-027), removing the multi-region hub/peering problem Azure and AWS both had to solve explicitly; and Cloud Pub/Sub natively combines topic-style fan-out, per-order ordering, and dead-lettering in a single product (ADR-025), where Azure needed one integrated product (Service Bus) and AWS needed two separate ones (EventBridge + SQS).

## 1. Service Mapping

| Logical Component | GCP Service | Tier / Notes | Why |
| --- | --- | --- | --- |
| CDN / Edge | Cloud CDN + Global External Application Load Balancer | Single global anycast IP, Cloud Armor built in | Closes the "no CDN in front of static assets" gap named in `current-state.md` §1 (see ADR-028) |
| API Gateway | Google Cloud API Gateway | One regional instance per active region | Single ingress, Identity Platform token validation, per-region to avoid a global-instance bottleneck (see ADR-028) |
| Identity Provider | Google Cloud Identity Platform | Single project-level configuration, multi-tenancy for logical EU/US/APAC separation | Purpose-built consumer CIAM, not a workforce directory repurposed for millions of retail customers (see ADR-026) |
| Storefront & Catalog Service | Cloud Run | One service per active region | Fast, per-request elastic scaling for the 25x/5-minute requirement, no cluster to operate (see ADR-021) |
| Cart Service | Cloud Run | Same Cloud Run service as Storefront & Catalog | Session-scoped, same scaling shape as Storefront & Catalog (see ADR-021) |
| Checkout & Payment Service | Cloud Run | **Separate, dedicated Cloud Run service** per active region, own subnet + VPC Service Controls perimeter | PCI isolation as a structural network and control-plane property, not just a policy statement (see ADR-021) |
| Inventory & Order Orchestration Service | Google Cloud Workflows + Cloud Run | One workflow definition per active region, Cloud Run-backed steps | Native, managed saga-state tracking, retry, and compensation  no long-running process needed to hold saga state (see ADR-024) |
| Global Catalog Read Store | Cloud SQL for PostgreSQL (cross-region read replicas) + Cloud Memorystore for Redis | US primary, EU/APAC read replicas | Same PostgreSQL engine family as every other track, native cross-region replication matches ADR-003's single-writer/multi-reader topology (see ADR-023) |
| Regional Transactional Store (×3) | Cloud SQL for PostgreSQL | HA (regional), one independent instance per region | Same engine family, no schema conversion, all three regions greenfield (see ADR-022) |
| Event Bus | Google Cloud Pub/Sub | One topic per event type + per-consumer subscriptions with ordering keys, per active region | Native topic/subscription fan-out, per-order ordering, and dead-lettering in a single product, scoped to Order Orchestration only per ADR-002 (see ADR-025) |
| Payment Gateway | Third-party, unchanged | External, PCI Level 1, hosted-fields tokenization | Unchanged from current state (`current-state.md` §5); this platform's only role is *not* being in this data path (ADR-004) |
| Session / catalog cache | Cloud Memorystore for Redis | One instance per active region | Direct managed replacement for the self-managed Redis named in `current-state.md` §1 |
| Product search | (Deferred  see Section 14) | Not yet mapped | GCP's managed search offerings are evaluated during the cost-analysis and IaC-buildout stages rather than assumed here (see Section 14) |
| Secrets | Secret Manager |  | Every service authenticates against this via IAM service accounts instead of embedded secrets |
| Observability | Cloud Monitoring + Cloud Trace + Cloud Logging | One log/metrics scope per region | Closes the "no distributed tracing, no business-level signals" gap named in `current-state.md` §4 |
| Network | Single global Google Cloud VPC network | Regional subnets, no peering/hub required | Genuine any-to-any multi-region connectivity without a manual peering mesh or hub product (see ADR-027) |
| Fulfillment / Warehouse | Existing system, unchanged | Out of scope | `problem-statement.md` §5  this design only produces the `order-confirmed` event it already consumes |

## 2. Compute  Customer-Facing Regional Services (see ADR-021)

Storefront & Catalog, Cart, and Checkout & Payment all run on Cloud Run, chosen specifically because its per-request autoscaling can react to the 20–25x, single-digit-minute traffic ramps `requirements.md` §1 documents as having actually happened, without handing Solstice's 22-person engineering org a VM fleet or a Kubernetes cluster to operate. Storefront & Catalog and Cart share one Cloud Run service per active region; Checkout & Payment gets its own, separate service per region, reached through its own dedicated Serverless VPC Access connector and sitting inside its own VPC Service Controls perimeter  the structural implementation of the "isolated network segment" ADR-001 and ADR-002 already decided Checkout & Payment needs. The in-memory catalog cache that made the current-state fleet's cold starts slow (`current-state.md` §2) is removed from the request path entirely; Storefront & Catalog reads through Cloud Memorystore for Redis in front of its regional Global Catalog read replica (Section 5), and a cache miss  not a cold container  is the only path that touches the database. A configured minimum-instance floor (see ADR-021's Proposed Configuration) trades away part of Cloud Run's scale-to-zero cost advantage specifically to avoid cold-start risk during the opening seconds of a named peak event.

## 3. Compute  Inventory & Order Orchestration (see ADR-024)

Order Orchestration's saga (reserve inventory → confirm payment → create order → hand off to fulfillment) runs on Google Cloud Workflows, one workflow definition per active region, triggered off the Event Bus (Section 9) via Eventarc and executing small, single-purpose Cloud Run services per step. This is the one place this document's GCP answer is architecturally different from a mechanical restatement of the Azure or AWS pattern  Cloud Workflows is a managed, durable orchestration engine that tracks saga state, retries, and compensation natively, removing the need for a long-running consumer process to hold that state itself, the same category of answer Step Functions is on the AWS track. See ADR-024 for the full reasoning.

## 4. Database  Regional Transactional Store (see ADR-022)

Cart, Checkout, and Order data runs on Cloud SQL for PostgreSQL, one independent, HA (regional) instance per active region, with no cross-region replication between them, directly implementing ADR-003's regional-primary partitioning. AlloyDB for PostgreSQL was considered and set aside for this store specifically  its throughput advantages pay off at a write scale this workload doesn't reach per region, and it's a materially newer product than Cloud SQL. Cloud Spanner was rejected outright, not as a close call  its entire value proposition (synchronous multi-region consistency) doesn't apply to a store that deliberately has no cross-region replication at all. See ADR-022.

## 5. Database  Global Catalog (see ADR-023)

The catalog uses the same PostgreSQL engine family, but a different topology: a single-writer primary in the US region with Cloud SQL's native asynchronous cross-region read replicas in EU and APAC, directly implementing ADR-003's single-writer/multi-region-read pattern. Cloud Memorystore for Redis sits in front of each region's replica as a read-through accelerator for the highest-traffic product pages  a cache, not the replication mechanism itself. Cloud Spanner was a genuine, close alternative here (see ADR-023's Rationale) and is worth revisiting if a future revision of this case study tightens the catalog's consistency requirement.

## 6. Networking

- **Single global VPC**: one Google Cloud VPC network (custom-mode) spans all three active regions, with regional subnets in US, EU, and APAC  chosen over a peered multi-VPC design specifically because GCP's VPC networks are a global resource, removing the hub-product problem Azure (Virtual WAN) and AWS (Transit Gateway) both had to solve explicitly. See ADR-027.
- **Regional subnets**: dedicated subnets per region for the Storefront & Catalog/Cart Cloud Run service, the Checkout & Payment Cloud Run service, Order Orchestration's Cloud Workflows step compute, and Cloud SQL private-IP database resources.
- **Egress control**: every subnet routes default egress through Cloud NGFW (or Secure Web Proxy) with a default-deny hierarchical firewall policy, plus Cloud NAT for controlled internet egress  no direct-to-internet path from any application subnet. Unlike a hub product, there is no bundled firewall to rely on implicitly here at all, so this is provisioned explicitly per region regardless (see ADR-027's Trade-off).

### 6.1 Network Addressing Plan

Non-overlapping ranges across all three regions, consistent with the other two tracks' addressing plans, even though GCP's global VPC means re-addressing later is less of a forcing function than it was for AWS's Transit Gateway peering.

| Region | Subnet | Range | Purpose |
| --- | --- | --- | --- |
| US (`us-central1`) | `subnet-storefront-cart-us` | 10.10.1.0/24 | Storefront & Catalog / Cart Cloud Run connector (ADR-021) |
| | `subnet-checkout-us` | 10.10.2.0/24 | Checkout & Payment Cloud Run connector  PCI-isolated (ADR-021) |
| | `subnet-orchestration-us` | 10.10.3.0/24 | Order Orchestration Cloud Workflows step compute (ADR-024) |
| | `subnet-db-us` | 10.10.4.0/24 | Regional Transactional Store + Global Catalog primary (ADR-022, ADR-023) |
| | `subnet-lb-us` | 10.10.5.0/24 | API Gateway / load-balancer backend connectivity (ADR-028) |
| EU (`europe-west1`) | `subnet-storefront-cart-eu` | 10.20.1.0/24 | Same pattern as US |
| | `subnet-checkout-eu` | 10.20.2.0/24 | |
| | `subnet-orchestration-eu` | 10.20.3.0/24 | |
| | `subnet-db-eu` | 10.20.4.0/24 | Holds the EU Global Catalog **read replica** (ADR-023), not a writable primary |
| | `subnet-lb-eu` | 10.20.5.0/24 | |
| APAC (`asia-southeast1`) | `subnet-storefront-cart-apac` | 10.30.1.0/24 | Same pattern as US |
| | `subnet-checkout-apac` | 10.30.2.0/24 | |
| | `subnet-orchestration-apac` | 10.30.3.0/24 | |
| | `subnet-db-apac` | 10.30.4.0/24 | Holds the APAC Global Catalog **read replica** (ADR-023) |
| | `subnet-lb-apac` | 10.30.5.0/24 | |

`subnet-checkout-*` in every region carries its own hierarchical firewall policy, allow-listing only the specific traffic Checkout & Payment actually needs (inbound from `subnet-lb-*`, outbound to `subnet-db-*` and the external Payment Gateway) and denying everything else, including traffic from `subnet-storefront-cart-*` in the same region  the concrete enforcement behind ADR-021's "isolated network segment," reinforced by the VPC Service Controls perimeter named there.

## 7. Global Entry  CDN/Edge and API Gateway (see ADR-028)

Cloud CDN, layered on a Global External Application Load Balancer, is the single global entry point: a single anycast IP, latency-based routing to the nearest healthy active region, static-asset caching, and Cloud Armor for WAF/DDoS absorption  the direct fix for `current-state.md` §1's "no CDN in front of static assets" gap. Behind it, each region runs its own Google Cloud API Gateway instance, validating Identity Platform tokens (Section 8) and applying quota/rate-limit policies before any request reaches Storefront & Catalog, Cart, or Checkout & Payment, routed over Serverless VPC Access to each region's Cloud Run services. See ADR-028.

## 8. Identity and Security

- Google Cloud Identity Platform issues OAuth2/OIDC tokens for customer sign-in, validated at each region's API Gateway  a single project-level configuration rather than per-region pools, with multi-tenancy used for logical EU/US/APAC separation pending verification of Identity Platform's exact data-location commitments (see ADR-026).
- Every GCP service in the request path (API Gateway, Cloud Run, Cloud SQL, Memorystore) is reached over private VPC connectivity via Serverless VPC Access, never the public internet.
- Secret Manager holds every credential and certificate; IAM service accounts let Cloud Run services, Cloud Workflows executions, and other components authenticate without embedded secrets.
- Checkout & Payment's own Cloud Run service, dedicated subnet, and VPC Service Controls perimeter (Section 6) are the structural PCI isolation boundary  cardholder data never reaches it anyway, since ADR-004's client-side hosted fields send it straight from the customer's browser to the Payment Gateway, but the isolated boundary still narrows blast radius for everything else that *does* run there.
- Security Command Center provides workload-level threat detection and posture management across the project.

## 9. Messaging  Google Cloud Pub/Sub

Order events (`order-placed`, `inventory-reserved`, `payment-confirmed`, `order-confirmed`, `order-cancelled`, `inventory-released`) route through one set of Pub/Sub topics per active region, with one subscription per consumer per event type  matching the regional-primary shape of the orders that produce them (ADR-003) rather than one global topic set. Ordering keys (key = order ID) plus native dead-letter topics mean a failed or unprocessable order event doesn't silently disappear or get processed out of sequence, all inside one product rather than two. See ADR-025.

## 10. Observability

Every service ships logs and metrics to Cloud Logging and Cloud Monitoring, and distributed traces to Cloud Trace, directly closing the two gaps `current-state.md` §4 named: no distributed tracing across service boundaries, and no business-level signals (checkout success rate, cart-to-order conversion latency) alongside the infrastructure metrics that already existed. Alerts are tied to the signals that actually matter operationally: Pub/Sub dead-letter topic message count, Cloud SQL replication lag on the Global Catalog replicas, Cloud Run instance count approaching its configured maximum during a named peak event (an early warning that the ceiling itself may need raising before the event, not during it), and Cloud Workflows execution failure rate for the order-orchestration saga.

## 11. Regional-Outage Response

As with the other two tracks, this is deliberately not framed as a "disaster recovery" section  this design has no primary region; all three are active all the time, for latency, not failover (`architecture-options-and-styles.md` §3). A regional outage here doesn't trigger a failover  it means one region is temporarily unreachable while the other two continue serving their own customers unaffected, and the Global External Application Load Balancer's health checks simply stop routing new traffic to the unhealthy region's API Gateway backend.

| Scenario | What happens | What doesn't |
| --- | --- | --- |
| One region's Storefront & Catalog/Cart/Checkout compute becomes unhealthy | The load balancer's health checks detect it and stop routing new customer traffic there; the other two regions are unaffected | No cross-region compute failover  a customer normally served by the down region gets routed to the next-nearest healthy region instead, at a latency cost `requirements.md` §3's targets don't cover for that window, an accepted, named trade-off |
| One region's Regional Transactional Store becomes unavailable | Customers whose home region that is lose write availability for in-flight carts/orders until it recovers (ADR-003's already-accepted trade-off, ADR-022 implements it) | No automatic cross-region write failover  building one would mean abandoning regional-primary partitioning or building active-active multi-master for financial data, both rejected in ADR-003 |
| The US region (Global Catalog primary) becomes unavailable | EU and APAC continue serving their local read replicas  catalog *reads* are unaffected; catalog *writes* (merchandising/back-office) are blocked until an operator manually promotes a replica (ADR-023) | No automatic replica promotion  a deliberate choice to avoid a split-brain write scenario over a catalog-write outage that doesn't stop customers from browsing or completing an in-flight cart |

## 12. Infrastructure as Code

Terraform is the primary IaC option for this track, not a GCP-native tool  unlike Azure (Bicep) and AWS (CloudFormation/CDK), GCP's own first-party IaC option (Google Cloud Deployment Manager) has been de-emphasized in favor of Terraform across the GCP ecosystem, and Terraform already has first-class, actively-maintained support for Cloud Run, Cloud Workflows, the global VPC model, and every other resource type used above. This also means the cross-platform comparison work in the decision-matrix stage (Step 9) gets a head start on this track specifically, since the same tool is both this track's primary IaC choice and the tool reserved for that later cross-platform work on the other two tracks.

## 13. Alignment Check

A gut-check against Google Cloud's Architecture Framework pillars before moving on:

| Pillar | How this design addresses it |
| --- | --- |
| Reliability | Regional HA compute and database per region, three genuinely independent active regions (not one primary + standby), Pub/Sub dead-lettering, Cloud Workflows' durable execution history for in-flight sagas |
| Security | Identity Platform token validation + private VPC connectivity everywhere, Secret Manager-managed credentials, a structurally isolated PCI network segment plus VPC Service Controls perimeter for Checkout & Payment |
| Cost Optimization | Deferred to the cost/risk analysis stage  sizing above is directional, not final; Cloud Run is chosen specifically to avoid paying peak-capacity VM prices year-round, the direct answer to `requirements.md` §3's 30%-cost-reduction target; Cloud Workflows' per-step pricing needs modeling against fixed compute before that stage concludes (ADR-024) |
| Operational Excellence | Terraform IaC, centralized per-region observability via Cloud Monitoring/Trace/Logging, a network topology (single global VPC) chosen specifically to remove peering-mesh maintenance entirely for a lean engineering org |
| Performance Efficiency | Cloud Run's per-request autoscaling reacts inside the 5-minute elasticity target; Cloud CDN + regional API Gateway keeps API-policy enforcement close to the services it protects instead of round-tripping to one global instance |

## 14. Explicitly Deferred

- Exact compute/database sizing and cost modeling  cost-analysis stage
- Final platform recommendation  Step 9, after this and the other two tracks are compared
- Detailed IAM service-account/role definitions
- Product search service mapping  GCP's managed search options (e.g., Vertex AI Search, or a self-managed Elasticsearch-compatible option) are evaluated once real catalog scale and query patterns exist, rather than defaulted to here; deliberately left open rather than filled in with an unverified guess
- Terraform modules themselves (built once, during the migration-roadmap stage, for whichever platform is chosen)
- Verification of Identity Platform's exact per-tenant data-location guarantees (ADR-026)  a concrete open item for Step 9/Step 11, not smoothed over
- Detail diagrams for this step (mirroring Steps 6 and 7's per-ADR diagrams)  not yet built for this step

## 15. Diagrams

Not yet built for this step  to follow the same pattern as Steps 6 and 7 (an overview implementation diagram plus per-ADR detail diagrams where warranted), once drafted and reviewed against this document and ADR-021 through ADR-028.
