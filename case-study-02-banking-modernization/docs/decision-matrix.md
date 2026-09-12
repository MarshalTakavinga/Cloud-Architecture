# Step 10: Decision Matrix (Azure / AWS / GCP / Private Cloud)

## Purpose

[Steps 6](azure-implementation.md)–[9](private-cloud-implementation.md) built four independent, equally rigorous implementations of the same nine-component logical design ([Step 5](logical-design.md)). This step scores all four against `requirements.md`'s own priority weighting, decided *before* any platform-specific work began — the weights are not chosen to produce a preferred answer.

## Criteria and Weights

Directly traced to `requirements.md`'s "Priority Weighting" section, which lists these six factors in this order and names regulatory/resiliency fit as highest:

| # | Criterion | Weight | Traced To |
|---|---|---|---|
| 1 | Regulatory/resiliency fit | 25% | Driver 2 (OCC heightened standards); NFR-1, NFR-2, NFR-7 |
| 2 | Real-time payments delivery within 18 months | 20% | Driver 1; the board-committed timeline constraint |
| 3 | Fraud-detection latency fit | 15% | Driver 4; NFR-4 |
| 4 | Cost trajectory impact | 15% | Driver 3; NFR-9 |
| 5 | Operational/skills fit | 15% | The cloud-skills-gap constraint |
| 6 | Data residency and portability | 10% | NFR-6; vendor lock-in exposure |

## Scoring (1–5 scale, 5 = strongest fit)

| Criterion (weight) | Azure | AWS | GCP | Private Cloud |
|---|---|---|---|---|
| Regulatory/resiliency fit (25%) | **5** | 4 | 3.5 | 3 |
| Real-time delivery in 18 months (20%) | 4 | **4.5** | 3.5 | 2.5 |
| Fraud-detection latency fit (15%) | 4 | 4 | 4 | **5** |
| Cost trajectory impact (15%) | 3.5 | 3.5 | **4.5** | 3.5 |
| Operational/skills fit (15%) | 4.5 | **4.5** | **4.5** | 2.5 |
| Data residency and portability (10%) | 4 | 4 | 4 | **5** |
| **Weighted Total** | **4.25 / 5.00 (85.0%)** | 4.10 / 5.00 (82.0%) | 3.93 / 5.00 (78.5%) | 3.40 / 5.00 (68.0%) |

*(Weighted totals independently verified by direct calculation, not estimated — see [ADR-029](../adr/ADR-029-cloud-platform-selection.md) for the full rationale behind each score.)*

## Why Azure Wins — and Why It Isn't a Landslide

Azure wins primarily on the single highest-weighted criterion: **[ADR-006](../adr/ADR-006-azure-ledger-of-intent-database.md)'s SQL Ledger feature is the only database-native, cryptographically verifiable immutability guarantee among all four tracks.** AWS and GCP both rely on object-storage WORM policies after Amazon QLDB's 2024 discontinuation ([ADR-012](../adr/ADR-012-aws-ledger-of-intent-database.md), [ADR-018](../adr/ADR-018-gcp-ledger-of-intent-database.md)) — real, defensible controls, but a database-level cryptographic chain is a stronger, more directly examiner-legible answer to "prove this record wasn't altered," which is exactly what the highest-weighted criterion is built around. Azure also carries the strongest overall operational-fit score alongside AWS and GCP, all three of which get a fully managed serverless-container platform.

Azure does **not** win cleanly on every criterion, and this matrix does not pretend otherwise:

- **AWS scores highest on the 18-month delivery criterion**, specifically because [ADR-016](../adr/ADR-016-aws-landing-zone-and-segmentation.md)'s enrollment approach for the 2021 account requires no rebuild of those workloads — a genuine schedule advantage the other three tracks don't share, since Azure and GCP both require a full cross-cloud replatform of that legacy footprint, and private cloud's hardware procurement lead time is a schedule risk of its own.
- **GCP scores highest on cost trajectory**, because [ADR-019](../adr/ADR-019-gcp-messaging.md)'s single-product Pub/Sub answer avoids both Azure's Premium-tier Service Bus cost ([ADR-007](../adr/ADR-007-azure-messaging.md)) and AWS's two-product SNS+SQS FIFO spend ([ADR-013](../adr/ADR-013-aws-messaging.md)).
- **Private cloud scores highest on fraud-detection latency and on data residency/portability** — [ADR-026](../adr/ADR-026-private-cloud-network-topology.md)'s same-facility placement genuinely eliminates the WAN hop every hyperscaler track carries, and full data/infrastructure ownership is the strongest portability story of the four. It loses overall specifically because it scores lowest on the two highest-weighted criteria: [ADR-024](../adr/ADR-024-private-cloud-compute-platform.md)'s unavoidable Kubernetes-operations burden and [ADR-025](../adr/ADR-025-private-cloud-database.md)'s weaker, application-layer-only audit immutability both work directly against the regulatory/resiliency criterion that carries the most weight, and hardware procurement lead time is a real risk against the hard 18-month deadline.

## What This Matrix Deliberately Does Not Resolve

Exact dollar costs are a Step 13 exercise, not this one — "cost trajectory impact" here is a directional, qualitative score based on each track's own named cost characteristics (Premium messaging tiers, capex vs. opex, multi-account/multi-project governance overhead), not a dollar-for-dollar model. The disposition of the 2021 AWS account workloads under the *winning* platform is carried forward to [Step 11](target-architecture.md) and [Step 12](migration-roadmap.md), not decided here.
