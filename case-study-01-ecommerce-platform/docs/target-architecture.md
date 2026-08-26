# Target Architecture  Solstice Retail Group

Step 10 turns Step 9's decision into the architecture Solstice actually builds toward. This document doesn't re-derive what `docs/aws-implementation.md` and ADR-013 through ADR-020 already decided in full depth  it states what's now final versus what Step 9 already flagged as still open, and reads the target state as one coherent system rather than eight separate ADRs.

## 1. The Decision, Restated Once

Per ADR-029, **Amazon Web Services is the target platform.** `docs/aws-implementation.md` is the target architecture document; ADR-013 through ADR-020 are the target-state ADRs. Nothing in this document changes a single decision made there  Step 10's job is to confirm what's final, carry forward what's still explicitly open, and set up Step 11's migration plan, not to re-litigate Step 9.

## 2. Target Architecture at a Glance

| Layer | Target Service | Decided In |
| --- | --- | --- |
| Global entry (CDN/Edge + API Gateway) | Amazon CloudFront + regional Amazon API Gateway (REST, per-region) | ADR-020 |
| Identity | Amazon Cognito, one regional User Pool per active region | ADR-018 |
| Storefront & Catalog / Cart | Amazon ECS on AWS Fargate, one service per active region | ADR-013 |
| Checkout & Payment | Amazon ECS on AWS Fargate, dedicated service + subnet per region | ADR-013 |
| Inventory & Order Orchestration | AWS Step Functions (Standard Workflow) + AWS Lambda, one state machine per region | ADR-016 |
| Regional Transactional Store | Amazon RDS for PostgreSQL, Multi-AZ, one instance per region, no cross-region replication | ADR-014 |
| Global Catalog | Amazon RDS for PostgreSQL, US primary + EU/APAC cross-region read replicas, ElastiCache for Redis in front | ADR-015 |
| Event Bus | Amazon EventBridge + Amazon SQS (FIFO), one bus + per-consumer queues per region | ADR-017 |
| Network | AWS Transit Gateway per region, inter-region peered, AWS Network Firewall for egress | ADR-019 |
| Payment Gateway | Third-party, unchanged, client-side hosted tokenization | ADR-004 |
| Observability | Amazon CloudWatch + AWS X-Ray | `aws-implementation.md` §10 |
| IaC (target-state) | AWS CloudFormation / AWS CDK | `aws-implementation.md` §12 |

## 3. What This Design Actually Fixes, Traced to the Forcing Functions

Restating each of `problem-statement.md` §3's four forcing functions against the specific target-architecture mechanism that closes it  not as a recap, but as the acceptance criteria Step 11's migration has to actually hit before this design is considered done:

- **The Black Friday connection-pool exhaustion outage** is closed structurally, not papered over with bigger instances: Storefront & Catalog and Cart run on Fargate with target-tracking autoscaling that no longer opens a new database connection pool per instance against a single shared RDS server (ADR-013), and the in-memory catalog cache that made cold starts slow is removed from the request path entirely in favor of ElastiCache-fronted reads (`aws-implementation.md` §2). A repeat of the exact failure mode  autoscaling making database contention worse, not better  is structurally prevented, not just less likely.
- **The ~2.1s EU page-load gap and GDPR data-residency requirement** are closed together: CloudFront + regional API Gateway (ADR-020) puts a CDN in front of static assets for the first time, and the EU Regional Transactional Store (ADR-014) plus EU Cognito User Pool (ADR-018) keep EU customer cart/checkout/order/identity data resident in the EU region as the structural default, not a policy statement layered on afterward.
- **The PCI-DSS finding** is closed by Checkout & Payment's dedicated ECS service, dedicated subnet, and security group (ADR-013), combined with ADR-004's client-side hosted tokenization  cardholder data never transits Solstice's application tier at all, closing the exact gap the QSA's finding named (`current-state.md` §3).
- **Rising unit economics** get a directional answer here (Fargate's pay-for-what-you-use model, ADR-013) with the actual number deferred to Step 12 on purpose  `requirements.md` §3's 30% target is a modeling exercise, not something this document should assert without showing the work.

## 4. What Step 9 Left Explicitly Open, Carried Forward Here

`docs/decision-matrix.md` §5 and `docs/aws-implementation.md` §14 both named real, unresolved items rather than treating the platform decision as closing every question. This document doesn't resolve them either  it states plainly which stage each belongs to, so nothing is silently dropped between Step 9 and Step 11:

- **The US-region cutover is the accepted trade-off of this decision, not yet planned.** ADR-029's Trade-off section names it explicitly: Step 11 (next) is where the actual phased plan gets built. Nothing about the target architecture above assumes an instant or risk-free transition.
- **Exact compute/database sizing and cost modeling**  Step 12.
- **CloudFormation/CDK templates themselves**  built once, during Step 11, not before a migration plan exists to build them against.
- **Detailed IAM role/permission definitions**  an implementation-phase task, not a Step 10 architecture decision.
- **Detail diagrams for the AWS track's own implementation**  the AWS ADRs (013–020) already have their own reviewed, saved diagrams (see each ADR's reference note); a single consolidated target-architecture diagram is a candidate for Step 11 if the migration roadmap benefits from one, not manufactured here for its own sake.

## 5. What Changes From "One of Three Tracks" to "The Target"

Three things are true now that weren't true when `docs/aws-implementation.md` was written, worth stating explicitly since the document's own framing ("nothing here is the final platform choice") is now out of date on purpose:

1. **AWS's known weaknesses are now accepted costs, not comparison notes.** ADR-019's Network Firewall gap (not bundled into Transit Gateway) and ADR-017's two-product messaging shape (EventBridge + SQS) are no longer "here's how AWS compares to Azure/GCP"  they're now line items Step 11's rollout and Step 12's cost model have to actually account for.
2. **The Azure and GCP tracks are not discarded.** `docs/azure-implementation.md` and `docs/gcp-implementation.md`, and their respective ADR sets, remain in the repository as the documented runner-up and third-place comparisons  not because they might still be chosen, but because `docs/decision-matrix.md`'s reasoning is only auditable as long as the alternatives it compared against are still visible in full, not deleted once a winner is picked.
3. **Every "final platform recommendation deferred to Step 9" note across all three implementation docs is now resolved by ADR-029.** No further ADR needs to re-ask which platform Solstice is building on.

## 6. What's Next: Step 11 (Migration Roadmap)

The target architecture is fixed. What's not yet decided is the order and mechanism of getting from `current-state.md`'s single-region monolith to the architecture above without repeating the outage this whole case study exists to prevent. That's Step 11's exact job: phasing (which region, which component, in what order), the cutover mechanism for the US region specifically (the one region with real production traffic to migrate), and a rollback strategy for when  not if  something in a phased cloud migration doesn't go as planned on the first attempt.
