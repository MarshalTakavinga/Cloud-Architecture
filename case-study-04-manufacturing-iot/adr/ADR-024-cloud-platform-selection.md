# ADR-024: Cloud Platform Selection — Google Cloud (with Conditions)

**Status:** Approved, with conditions and review triggers
**Date:** Step 9 of the Case Study 4 pipeline

## Context

[Steps 6](../docs/azure-implementation.md)–[8](../docs/gcp-implementation.md) implemented the same [Step 5](../docs/logical-design.md) design on Azure ([ADR-006](ADR-006-azure-edge-platform.md)–[ADR-011](ADR-011-azure-network-identity-and-deployment.md)), AWS ([ADR-012](ADR-012-aws-edge-platform.md)–[ADR-017](ADR-017-aws-network-identity-and-deployment.md)), and GCP ([ADR-018](ADR-018-gcp-edge-platform.md)–[ADR-023](ADR-023-gcp-network-identity-and-deployment.md)), each including the plant edge. [`docs/decision-matrix.md`](../docs/decision-matrix.md) scores them against `requirements.md`'s weighting. That weighting was refined in one disclosed, mechanical way: a 10% genealogy-integrity criterion was added and the original weights scaled by 0.9.

## Decision

Kestrel's industrial data platform is built on **Google Cloud**:
- **Edge:** Google Distributed Cloud (software-only, bare metal) with Manufacturing Connect edge
- **Cloud:** Pub/Sub, Manufacturing Data Engine, Bigtable and BigQuery, Dataflow, Vertex AI, and Cloud SQL
- **Regions:** us-east5 for US/MX and europe-west3 for Plants 11–12

GCP scores **3.95/5.00 (79.0%)**, ahead of Azure at 3.83 (76.6%) and AWS at 3.34 (66.8%).

The margin over Azure is narrow, so the decision is **conditional**. The conditions below target GCP's two weakest scores, and the review triggers name the evidence that would reopen the choice.

## Scoring Rationale, Criterion by Criterion

1. **OT security and edge fit (22.5%). GCP 4.5, Azure 4, AWS 3.**
   - **GCP:** GDC keeps local Kubernetes operations, deployments, and Config Sync running through a disconnection with no documented time limit, and it has native multi-node HA ([ADR-018](ADR-018-gcp-edge-platform.md)).
   - **Azure:** equal on HA, but held back by IoT Operations' documented 72-hour offline maximum ([ADR-006](ADR-006-azure-edge-platform.md)). The mitigation keeps critical functions independent of it but does not remove it.
   - **AWS:** its HA pattern is an active/passive Pacemaker/DRBD pair that AWS labels "for testing and demonstration purposes only" ([ADR-012](ADR-012-aws-edge-platform.md)).
2. **Industrial protocol and edge ecosystem (18%). GCP 4.5, AWS 4, Azure 3.5.**
   - **GCP:** MCe's 270+ protocols and native Sparkplug B honor [ADR-002](ADR-002-plant-data-integration-pattern.md) as written and remove the protocol gateways.
   - **AWS:** SiteWise Edge is the most mature dedicated gateway.
   - **Azure:** IoT Operations is the newest, and it publishes JSON/CloudEvents, not Sparkplug B.
3. **Genealogy integrity (10%). Azure 5, AWS 3.5, GCP 3.5.**
   - **Azure:** append-only ledger tables are engine-enforced ([ADR-010](ADR-010-azure-genealogy-store.md)). This is the same capability that decided Case Study 2.
   - **AWS and GCP:** grants, a trigger, a hash chain, and WORM storage ([ADR-016](ADR-016-aws-genealogy-store.md), [ADR-022](ADR-022-gcp-genealogy-store.md)). Tampering is detectable but not prevented.
4. **Ingestion and time-series economics (13.5%). AWS 3.5, Azure 3, GCP 3.** Directional only. AWS has no per-node edge platform fee. Azure pays a per-node fee on 36 nodes, fixed Event Hubs processing units, and two Fabric capacities. GCP stacks GDC, MCe, and broker licences at the edge, though its cloud side is lean.
5. **Analytics and ML fit (13.5%). GCP 4.5, Azure 4, AWS 3.5.** BigQuery + MDE + Vertex AI is the least build effort for a four-person team ([ADR-021](ADR-021-gcp-time-series-and-analytics.md)).
6. **Operational and skills fit (13.5%). Azure 4, GCP 3, AWS 2.5.** Azure has one edge vendor and one management plane. GCP has three edge vendors and a fully custom outbox ([ADR-019](ADR-019-gcp-store-and-forward-implementation.md)). On AWS, Kestrel would own HA clustering in 12 plants.
7. **Residency and portability (9%). GCP 4, Azure 3.5, AWS 3.5.** On GCP, Sparkplug B keeps the plant side standard, and VPC Service Controls give the strongest residency boundary ([ADR-023](ADR-023-gcp-network-identity-and-deployment.md)).

## Conditions (part of the decision, owned in Steps 10–11)

1. **Strengthen genealogy integrity beyond the scored baseline.** Nightly Merkle digests go to a Bucket-Locked bucket in a **separate project with a separate admin group**, so that no single privileged role can both alter the table and its evidence. OEMs are offered a monthly **independently verifiable digest**, and a quarterly integrity-verification drill is recorded in the audit log. This narrows, though it does not close, the gap with Azure's engine-level guarantee.
2. **Edge operations as a managed service from day one.** A single **managed-service provider contract** covers the GDC clusters, MCe, and the broker, with Litmus and the broker vendor as named subcontractors. This gives one incident owner per plant, which answers the three-vendor finding.
3. **The outbox is built first and tested hardest.** The Kestrel-built Outbox Service ([ADR-019](ADR-019-gcp-store-and-forward-implementation.md)) is the first engineering workstream. Its acceptance test suite (outage injection, backfill under the rate cap, lane starvation, and replay idempotency) must pass at the pilot plant before any wave rollout.
4. **Capacity guardrail.** The MCe tag headroom per instance is monitored, and any plant forecast to exceed about 80% of the 10K-tag limit within 12 months is planned for a second instance in advance.

## Review Triggers (reopen this ADR if any occur)

- **Cost.** Step 12's cost model shows GCP's edge licence stack (GDC + MCe + broker) exceeding Azure's equivalent run-rate by more than 20% over 5 years.
- **Audit.** An OEM customer's supplier-quality audit requires database-engine-level immutability for genealogy. The sensitivity analysis shows that weighting genealogy at 20% or more flips the result to Azure.
- **Vendor change.** Litmus or Google materially changes Manufacturing Connect's availability, licensing, or support model. Given the documented churn history on all three platforms, this trigger is written down deliberately.
- **Azure change.** Microsoft removes or materially relaxes IoT Operations' 72-hour offline limit. That would bring Azure level on the highest-weighted criterion and into a statistical tie.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Azure (3.83).** It is close and credible, and it is the better choice if genealogy audit evidence or edge operating simplicity dominate. It is rejected on the two highest-weighted criteria that define this case study: plant autonomy without a documented ceiling, and the industrial protocol ecosystem.
2. **AWS (3.34).** It has strong lane semantics and device identity, but running do-it-yourself edge HA in 12 plants without IT staff is disqualifying at this weighting.
3. **Split platforms: GCP for telemetry and Azure SQL Ledger for genealogy only.** Considered, because it would capture both tracks' best scores. Rejected because the operational, identity, network, and skills cost of running two clouds for a four-person data team outweighs the genealogy gain. Condition 1 captures most of that benefit within one platform.

## Consequences

- **Positive:** The chosen platform matches the core of this case study, the edge. Sparkplug B, the 270+ protocol drivers, and disconnection without a documented ceiling are exactly what Steps 1–5 asked for.
- **Negative / accepted trade-off:** Kestrel takes on the most edge integration of the three tracks: three vendors plus the custom outbox. Conditions 2 and 3 are the mitigation, and both are costed in Step 12.
- **Negative / accepted trade-off:** Genealogy immutability rests on controls and evidence, not on engine enforcement. Condition 1 and the audit review trigger keep that visible.
- **Portfolio note:** Case Studies 2 and 3 selected Azure, and Case Study 1 selected AWS. GCP winning here comes from the weighting, not from a wish for variety. The sensitivity table shows exactly what would have to be true for Azure to win instead.

## Addendum — Step 12 Trigger Test (cost)

[`docs/cost-and-risk-analysis.md`](../docs/cost-and-risk-analysis.md) tested the cost review trigger with the illustrative model in [`finance/TCO-Analysis.xlsx`](../finance/TCO-Analysis.xlsx).

- **Result:** GCP's five-year edge licence stack is about $2.10M. The trigger fires for any Azure IoT Operations price **below about $980 per node-month**, and Microsoft does not publish that price.
- **Effect on the decision:** re-scoring the economics criterion with this evidence (Azure 3.5, GCP 2.5) gives **Azure 3.90 against GCP 3.88**, which flips the decision.
- **Effect on the program:** the difference is about 2–3% of annual value, so the business case holds either way.

**Status change:** this ADR stays Approved, but it is **subject to gate G0 (commercial confirmation, by M3)**. Before any platform-specific commitment, binding quotes for GDC, Manufacturing Connect edge, the broker, and Azure IoT Operations are obtained and the model is re-run. If the trigger fires on real prices, the Step 9 economics criterion is re-scored and this decision is re-affirmed or reversed. Everything scheduled before G0 (Phase 0 security, sensors, tag mapping to ISA-95, and the genealogy recorder design) is platform-neutral, so neither outcome wastes work.
