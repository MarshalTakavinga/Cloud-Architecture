# AWS Implementation — Solstice Retail Group

This document implements the vendor-neutral logical design (Step 5) once on Amazon Web Services. It is one of three parallel implementations (Azure, AWS, GCP — no private-cloud track, per this case study's Scope Note) that will be scored against each other in a weighted decision matrix in Step 9 — nothing here is the final platform choice. Building it thoroughly rather than sketching it is what makes a fair comparison possible, matching the rigor Case Study 3 applied at this stage and matching this case study's own Step 6 (Azure).

Unlike the Azure track, this document is deliberately kept as a single file rather than split into a platform doc plus a separate per-service `application-architecture.md` — the per-service hosting, connectivity, and scaling detail is folded directly into Sections 2–5 and 9 below, since AWS's service boundaries (ECS services, Lambda functions, Step Functions state machines) map closely enough to the ADR-level detail that a second document would mostly repeat it.

One fact shapes several decisions below and is worth stating up front rather than re-deriving it eight times: **Solstice already runs on AWS.** `current-state.md` §1 names the current production stack directly — a single-region (`us-east-1`) EC2 Auto Scaling Group, a single Amazon RDS for PostgreSQL instance, self-managed Redis, self-managed Elasticsearch, S3 for static assets with no CDN in front of it. This AWS track is not a lift onto unfamiliar infrastructure the way the Azure and GCP tracks necessarily are — several of the services chosen below (RDS for PostgreSQL, in particular) are the same product Solstice already operates, and several self-managed pieces named in `current-state.md` §1 (Redis, Elasticsearch) have direct managed AWS equivalents. That familiarity is a genuine advantage worth carrying into Step 9's comparison, but it also means the US region's migration path carries real in-place cutover risk the EU and APAC regions (both greenfield) don't — flagged explicitly wherever it applies, rather than smoothed over to make the three platform tracks look more alike than they are.

## 1. Service Mapping

| Logical Component | AWS Service | Tier / Notes | Why |
| --- | --- | --- | --- |
| CDN / Edge | Amazon CloudFront | Global, with AWS Shield Standard included | Closes the "no CDN in front of static assets" gap named in `current-state.md` §1 (see ADR-020) |
| API Gateway | Amazon API Gateway | REST API, regional endpoint type, one instance per active region | Single ingress, Cognito token validation, per-region to avoid a global-instance bottleneck (see ADR-020) |
| Identity Provider | Amazon Cognito User Pools | One regional pool per active region (region-scoped resource, no single global tenant) | Purpose-built consumer CIAM, not a workforce directory repurposed for millions of retail customers (see ADR-018) |
| Storefront & Catalog Service | Amazon ECS on AWS Fargate | One service per active region | Fast, target-tracking elastic scaling for the 25x/5-minute requirement, no cluster to operate (see ADR-013) |
| Cart Service | Amazon ECS on AWS Fargate | Same ECS service as Storefront & Catalog | Session-scoped, same scaling shape as Storefront & Catalog (see ADR-013) |
| Checkout & Payment Service | Amazon ECS on AWS Fargate | **Separate, dedicated ECS service** per active region, own subnet | PCI isolation as a structural network property, not just a policy statement (see ADR-013) |
| Inventory & Order Orchestration Service | AWS Step Functions (Standard Workflow) + AWS Lambda | One state machine per active region, Lambda-backed steps | Native, managed saga-state tracking, retry, and compensation — no long-running process needed to hold saga state (see ADR-016) |
| Global Catalog Read Store | Amazon RDS for PostgreSQL (cross-region read replicas) + Amazon ElastiCache for Redis | US primary, EU/APAC read replicas | Same PostgreSQL engine already in production, native cross-region replication matches ADR-003's single-writer/multi-reader topology (see ADR-015) |
| Regional Transactional Store (×3) | Amazon RDS for PostgreSQL | Multi-AZ, one independent instance per region | Same engine Solstice already runs, no schema conversion (see ADR-014) |
| Event Bus | Amazon EventBridge + Amazon SQS (FIFO) | One custom bus + per-consumer FIFO queues, per active region | Topic-style fan-out plus per-order FIFO ordering and dead-lettering, scoped to Order Orchestration only per ADR-002 (see ADR-017) |
| Payment Gateway | Third-party, unchanged | External, PCI Level 1, hosted-fields tokenization | Unchanged from current state (`current-state.md` §5); this platform's only role is *not* being in this data path (ADR-004) |
| Session / catalog cache | Amazon ElastiCache for Redis | One cluster per active region | Direct managed replacement for the self-managed Redis named in `current-state.md` §1 |
| Product search | Amazon OpenSearch Service | One managed domain per active region, fed from the regional catalog read replica | Direct managed replacement for the self-managed 3-node Elasticsearch cluster named in `current-state.md` §1 |
| Secrets Manager | AWS Secrets Manager | — | Every service authenticates against this via IAM roles instead of embedded secrets |
| Observability | Amazon CloudWatch + AWS X-Ray + CloudWatch Logs Insights | One log group set per region | Closes the "no distributed tracing, no business-level signals" gap named in `current-state.md` §4 |
| Network | AWS Transit Gateway | One per active region, inter-region peered | Genuine any-to-any multi-region connectivity without a manual peering mesh (see ADR-019) |
| Fulfillment / Warehouse | Existing system, unchanged | Out of scope | `problem-statement.md` §5 — this design only produces the `order-confirmed` event it already consumes |

## 2. Compute — Customer-Facing Regional Services (see ADR-013)

Storefront & Catalog, Cart, and Checkout & Payment all run on Amazon ECS with AWS Fargate, chosen specifically because Application Auto Scaling's continuous target-tracking can react to the 20–25x, single-digit-minute traffic ramps `requirements.md` §1 documents as having actually happened, without handing Solstice's 22-person engineering org an EC2 fleet or a Kubernetes cluster to operate. Storefront & Catalog and Cart share one ECS service per active region; Checkout & Payment gets its own, separate service per region, in its own dedicated subnet — the structural implementation of the "isolated network segment" ADR-001 and ADR-002 already decided Checkout & Payment needs. As with the current production fleet (`current-state.md` §2), the in-memory catalog cache that made cold starts slow is removed from the request path entirely; Storefront & Catalog reads through Amazon ElastiCache for Redis in front of its regional Global Catalog read replica (Section 5), and a cache miss — not a cold container — is the only path that touches the database. See ADR-013's Proposed Configuration for task counts and scale-rule detail.

## 3. Compute — Inventory & Order Orchestration (see ADR-016)

Order Orchestration's saga (reserve inventory → confirm payment → create order → hand off to fulfillment) runs on AWS Step Functions, a Standard Workflow per active region, triggered off the Event Bus (Section 9) and executing small, single-purpose Lambda functions per step. This is the one place this document's AWS answer is architecturally different from the Azure track's equivalent, not just relabeled — Step Functions is a managed state-machine engine that tracks saga state, retries, and compensation natively, removing the need for a long-running consumer process to hold that state itself. See ADR-016 for the full reasoning.

## 4. Database — Regional Transactional Store (see ADR-014)

Cart, Checkout, and Order data stays on the same database engine it runs on today — Amazon RDS for PostgreSQL, one independent, Multi-AZ instance per active region, with no cross-region replication between them, directly implementing ADR-003's regional-primary partitioning. Amazon Aurora PostgreSQL-Compatible was considered and set aside for this store specifically — its storage-layer advantages pay off at a write scale this workload doesn't reach, per region, and standard RDS avoids operating a second database product alongside it. See ADR-014.

## 5. Database — Global Catalog (see ADR-015)

The catalog uses the same PostgreSQL engine, but a different topology: a single-writer primary in the US region with RDS's native asynchronous cross-region read replicas in EU and APAC, directly implementing ADR-003's single-writer/multi-region-read pattern. Amazon ElastiCache for Redis sits in front of each region's replica as a read-through accelerator for the highest-traffic product pages — a cache, not the replication mechanism itself. Amazon Aurora Global Database was a genuine, close alternative here (see ADR-015's Rationale) and is worth revisiting if a future revision of this case study tightens the catalog's consistency requirement.

## 6. Networking

- **Regional hubs**: AWS Transit Gateway in each of US, EU, and APAC, connected via inter-region Transit Gateway peering — chosen over three independently-peered VPCs specifically because this design needs genuine any-to-any regional connectivity (continuous catalog replication traffic, ADR-015), not the occasional-failover connectivity a two-region hub-and-spoke is built for. See ADR-019.
- **Regional VPCs**: one VPC per region, with dedicated subnets for the Storefront & Catalog/Cart ECS service, the Checkout & Payment ECS service, Order Orchestration's Lambda functions, database subnets, and API Gateway's VPC Link target subnet.
- **Egress control**: every VPC routes default egress through an AWS Network Firewall deployed in a dedicated inspection VPC attached to that region's Transit Gateway — no direct-to-internet path from any application subnet. Unlike Azure's Virtual WAN, this firewall is not bundled automatically into the hub product on AWS and has to be provisioned and priced explicitly (see ADR-019's Trade-off).

### 6.1 Network Addressing Plan

Non-overlapping ranges across all three regions up front, since Transit Gateway's inter-region peering means any region can, in principle, reach any other without a later re-addressing exercise.

| Region | VPC | Subnet | Range | Purpose |
| --- | --- | --- | --- | --- |
| US | 10.10.0.0/16 | subnet-storefront-cart | 10.10.1.0/24 | Storefront & Catalog / Cart ECS service (ADR-013) |
| | | subnet-checkout | 10.10.2.0/24 | Checkout & Payment ECS service — PCI-isolated (ADR-013) |
| | | subnet-orchestration | 10.10.3.0/24 | Order Orchestration Lambda functions (ADR-016) |
| | | subnet-db | 10.10.4.0/24 | Regional Transactional Store + Global Catalog primary (ADR-014, ADR-015) |
| | | subnet-apigw | 10.10.5.0/24 | API Gateway VPC Link / Network Load Balancer target subnet (ADR-020) |
| EU | 10.20.0.0/16 | subnet-storefront-cart | 10.20.1.0/24 | Same pattern as US |
| | | subnet-checkout | 10.20.2.0/24 | |
| | | subnet-orchestration | 10.20.3.0/24 | |
| | | subnet-db | 10.20.4.0/24 | Holds the EU Global Catalog **read replica** (ADR-015), not a writable primary |
| | | subnet-apigw | 10.20.5.0/24 | |
| APAC | 10.30.0.0/16 | subnet-storefront-cart | 10.30.1.0/24 | Same pattern as US |
| | | subnet-checkout | 10.30.2.0/24 | |
| | | subnet-orchestration | 10.30.3.0/24 | |
| | | subnet-db | 10.30.4.0/24 | Holds the APAC Global Catalog **read replica** (ADR-015) |
| | | subnet-apigw | 10.30.5.0/24 | |

`subnet-checkout` in every region carries its own security group, allow-listing only the specific traffic Checkout & Payment actually needs (inbound from `subnet-apigw`, outbound to `subnet-db` and the external Payment Gateway) and denying everything else, including traffic from `subnet-storefront-cart` in the same region — the concrete enforcement behind ADR-013's "isolated network segment."

## 7. Global Entry — CDN/Edge and API Gateway (see ADR-020)

Amazon CloudFront is the single global entry point: latency/geo-based routing to the nearest healthy active region, static-asset caching, AWS WAF, and AWS Shield Standard for DDoS absorption — the direct fix for `current-state.md` §1's "no CDN in front of static assets" gap. Behind it, each region runs its own Amazon API Gateway REST API (regional endpoint type, not edge-optimized), validating Cognito tokens (Section 8) and applying usage-plan rate limits before any request reaches Storefront & Catalog, Cart, or Checkout & Payment, routed over a VPC Link to each region's ECS services. See ADR-020.

## 8. Identity and Security

- Amazon Cognito issues OAuth2/OIDC tokens for customer sign-in, validated at each region's API Gateway via a Cognito authorizer — one regional User Pool per active region, since Cognito User Pools are region-scoped resources, not a single dedicated global tenant (see ADR-018).
- Every AWS service in the request path (API Gateway's VPC Link, ECS, RDS, ElastiCache) is reached over private VPC connectivity, never the public internet.
- AWS Secrets Manager holds every credential and certificate; IAM roles let ECS tasks, Lambda functions, and other components authenticate without embedded secrets.
- Checkout & Payment's own ECS service and subnet (Section 6) is the structural PCI isolation boundary — cardholder data never reaches it anyway, since ADR-004's client-side hosted fields send it straight from the customer's browser to the Payment Gateway, but the isolated boundary still narrows blast radius for everything else that *does* run there.
- Amazon GuardDuty and AWS Security Hub provide workload-level threat detection and posture management across the account.

## 9. Messaging — Amazon EventBridge + Amazon SQS

Order events (`order-placed`, `inventory-reserved`, `payment-confirmed`, `order-confirmed`, `order-cancelled`, `inventory-released`) route through one EventBridge custom bus per active region, with one rule per event type fanning out to a dedicated SQS FIFO queue per consumer — matching the regional-primary shape of the orders that produce them (ADR-003) rather than one global bus. FIFO ordering (message group ID = order ID) plus native dead-lettering means a failed or unprocessable order event doesn't silently disappear or get processed out of sequence. See ADR-017.

## 10. Observability

Every service ships logs and metrics to Amazon CloudWatch and distributed traces to AWS X-Ray, directly closing the two gaps `current-state.md` §4 named: no distributed tracing across service boundaries, and no business-level signals (checkout success rate, cart-to-order conversion latency) alongside the infrastructure metrics that already existed. Alerts are tied to the signals that actually matter operationally: SQS dead-letter queue depth, RDS replication lag on the Global Catalog replicas, ECS service task count approaching its configured ceiling during a named peak event (an early warning that the ceiling itself may need raising before the event, not during it), and Step Functions execution failure rate for the order-orchestration saga.

## 11. Regional-Outage Response

As with the Azure track, this is deliberately not framed as a "disaster recovery" section — this design has no primary region; all three are active all the time, for latency, not failover (`architecture-options-and-styles.md` §3). A regional outage here doesn't trigger a failover — it means one region is temporarily unreachable while the other two continue serving their own customers unaffected, and CloudFront's origin health checks simply stop routing new traffic to the unhealthy region's API Gateway origin.

| Scenario | What happens | What doesn't |
| --- | --- | --- |
| One region's Storefront & Catalog/Cart/Checkout compute becomes unhealthy | CloudFront's origin health checks detect it and stop routing new customer traffic there; the other two regions are unaffected | No cross-region compute failover — a customer normally served by the down region gets routed to the next-nearest healthy region instead, at a latency cost `requirements.md` §3's targets don't cover for that window, an accepted, named trade-off |
| One region's Regional Transactional Store becomes unavailable | Customers whose home region that is lose write availability for in-flight carts/orders until it recovers (ADR-003's already-accepted trade-off, ADR-014 implements it) | No automatic cross-region write failover — building one would mean abandoning regional-primary partitioning or building active-active multi-master for financial data, both rejected in ADR-003 |
| The US region (Global Catalog primary) becomes unavailable | EU and APAC continue serving their local read replicas — catalog *reads* are unaffected; catalog *writes* (merchandising/back-office) are blocked until an operator manually promotes a replica (ADR-015) | No automatic replica promotion — a deliberate choice to avoid a split-brain write scenario over a catalog-write outage that doesn't stop customers from browsing or completing an in-flight cart |

## 12. Infrastructure as Code

AWS CloudFormation (or the AWS CDK, for teams that prefer defining infrastructure in application code) is the primary IaC option for this track — AWS-native, first-class support for ECS, Step Functions, Transit Gateway, and every other resource type used above. As with the Azure track, Terraform is reserved for the cross-platform comparison work in the decision-matrix stage (Step 9): one tool spanning all three candidate platforms matters more at that stage than native fluency on any single one.

## 13. Alignment Check

A gut-check against the AWS Well-Architected Framework pillars before moving on:

| Pillar | How this design addresses it |
| --- | --- |
| Reliability | Multi-AZ compute and database per region, three genuinely independent active regions (not one primary + standby), SQS dead-lettering, Step Functions' durable execution history for in-flight sagas |
| Security | Cognito token validation + private VPC connectivity everywhere, Secrets Manager-managed credentials, a structurally isolated PCI network segment for Checkout & Payment |
| Cost Optimization | Deferred to the cost/risk analysis stage — sizing above is directional, not final; Fargate is chosen specifically to avoid paying peak-capacity EC2 prices year-round, the direct answer to `requirements.md` §3's 30%-cost-reduction target; Step Functions' transition-based pricing needs modeling against fixed compute before that stage concludes (ADR-016) |
| Operational Excellence | CloudFormation/CDK IaC, centralized per-region observability via CloudWatch/X-Ray, a network topology (Transit Gateway) chosen specifically to reduce peering-mesh maintenance for a lean engineering org |
| Performance Efficiency | Application Auto Scaling target-tracking reacts inside the 5-minute elasticity target; CloudFront + regional API Gateway keeps API-policy enforcement close to the services it protects instead of round-tripping to one global instance |

## 14. Explicitly Deferred

- Exact compute/database sizing and cost modeling — cost-analysis stage
- Final platform recommendation — Step 9, after this and the GCP implementation exist to compare against
- Detailed IAM role/permission definitions
- CloudFormation/CDK templates themselves (built once, during the migration-roadmap stage, for whichever platform is chosen)
- Detail diagrams for this step (mirroring Step 5 and Step 6's per-ADR diagrams) — not yet built for this step

## 15. Diagrams

Not yet built for this step — to follow the same pattern as Step 6 (an overview implementation diagram plus per-ADR detail diagrams where warranted), once drafted and reviewed against this document and ADR-013 through ADR-020.
