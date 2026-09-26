# Step 9: Decision Matrix (Azure / AWS / GCP)

## Purpose

[Steps 6](azure-implementation.md)–[8](gcp-implementation.md) built three independent implementations of the same 23-component logical design ([Step 5](logical-design.md)), each including the plant edge. This step scores them against the priority weighting that `requirements.md` recorded **before** any platform work began.

## Criteria and Weights, Including One Disclosed Refinement

`requirements.md` listed six provisional criteria in priority order and said they were "to be refined once options are on the table". Once the three tracks were built, one gap was obvious. **None of the six criteria measures genealogy integrity**, although driver 3 (serial-level traceability) is contract-gated and is where the three tracks differ most sharply: Azure's engine-enforced ledger compared with AWS and GCP's permission-and-trigger approach.

Leaving that out would bias the matrix *toward* the tracks that are weakest on it. The refinement is therefore made openly, and it is mechanical rather than hand-tuned:

- genealogy integrity is added at **10%**
- the six original weights are scaled by **0.9**, so their relative order and proportions are unchanged
- the result **without** the added criterion is also reported (see Sensitivity)

| # | Criterion | Original weight | **Weight used** | Traced to |
|---|---|---|---|---|
| 1 | OT security and edge-architecture fit (autonomy, outbound-only, HA, fleet management) | 25% | **22.5%** | Drivers 1 and 5; NFR-1, NFR-2, NFR-9 |
| 2 | Industrial protocol and edge ecosystem maturity (OPC UA, Sparkplug B, asset model, partners) | 20% | **18%** | ADR-002; the Plant 07 and Windows 7 plants; tag-model debt |
| 3 | Genealogy and traceability integrity *(added)* | — | **10%** | Driver 3; NFR-6, NFR-7, NFR-8; ADR-004 |
| 4 | Ingestion and time-series economics (qualitative until Step 12) | 15% | **13.5%** | NFR-3, NFR-4, NFR-12 |
| 5 | Analytics and ML fit (cloud training → edge inference, 4-person data team) | 15% | **13.5%** | Drivers 2 and 4 |
| 6 | Operational and skills fit (no edge or OT-security operations staff today) | 15% | **13.5%** | Skills assumption; the edge-sprawl risk |
| 7 | Data residency and portability | 10% | **9%** | NFR-10; the vendor-churn risk |

## Scoring (1–5 scale, 5 = strongest fit)

| Criterion (weight) | Azure | AWS | GCP |
|---|---|---|---|
| 1. OT security and edge fit (22.5%) | 4 | 3 | **4.5** |
| 2. Industrial protocol and edge ecosystem (18%) | 3.5 | 4 | **4.5** |
| 3. Genealogy integrity (10%) | **5** | 3.5 | 3.5 |
| 4. Ingestion and time-series economics (13.5%) | 3 | **3.5** | 3 |
| 5. Analytics and ML fit (13.5%) | 4 | 3.5 | **4.5** |
| 6. Operational and skills fit (13.5%) | **4** | 2.5 | 3 |
| 7. Residency and portability (9%) | 3.5 | 3.5 | **4** |
| **Weighted total** | 3.83 / 5.00 (76.6%) | 3.34 / 5.00 (66.8%) | **3.95 / 5.00 (79.0%)** |

*Totals were calculated directly, not estimated. The per-cell rationale is in [ADR-024](../adr/ADR-024-cloud-platform-selection.md).*

### Scoring notes (short form)

1. **OT/edge fit.**
   - **GCP (4.5):** Kubernetes HA plus local operations with **no documented disconnection limit**.
   - **Azure (4):** Kubernetes HA and the best single-vendor fleet tooling (Arc), but IoT Operations' documented **72-hour offline ceiling** sits exactly on NFR-1's floor. The mitigation does not remove it.
   - **AWS (3):** no ceiling and the best device identity, but HA is a do-it-yourself Pacemaker/DRBD pair that AWS itself labels demo-grade.
2. **Protocol and ecosystem.**
   - **GCP (4.5):** MCe brings 270+ protocols and native Sparkplug B, which is the only native match to ADR-002, and it removes the protocol gateways.
   - **AWS (4):** SiteWise Edge is the most mature dedicated industrial gateway.
   - **Azure (3.5):** IoT Operations is capable but the newest of the three, has no Sparkplug B, and needs gateways.
3. **Genealogy.**
   - **Azure (5):** append-only ledger tables are enforced by the database engine, with automatic digests.
   - **AWS and GCP (3.5 each):** PostgreSQL with grants and a trigger, plus a WORM archive. Tampering is detectable, but not prevented.
4. **Economics** (directional only; see Step 12).
   - **AWS (3.5):** no per-node edge platform fee, and on-demand streams.
   - **Azure (3):** a per-node IoT Operations fee across 36 nodes, fixed Event Hubs processing units, and two Fabric capacities.
   - **GCP (3):** per-vCPU GDC licences for 36 nodes, about 16 MCe licences, and broker licences stack at the edge, although the cloud side (serverless Pub/Sub, licence-free MDE) is lean.
5. **Analytics and ML.**
   - **GCP (4.5):** BigQuery + MDE (packaged ISA-95 pipeline) + Vertex AI is the lowest-effort stack for a four-person team.
   - **Azure (4):** Fabric unifies time series, lakehouse, and BI.
   - **AWS (3.5):** Flink is strong, but there are four analytics products to run.
6. **Operations and skills.**
   - **Azure (4):** one edge vendor and one management plane.
   - **GCP (3):** three edge vendors, the whole outbox is Kestrel-built, two deployment channels, and three DMZ services.
   - **AWS (2.5):** running HA clusters in 12 plants without IT staff.
7. **Residency and portability.**
   - **GCP (4):** Sparkplug B keeps the plant side standard, VPC Service Controls give the strongest residency boundary, and Beam and PostgreSQL are portable, although Pub/Sub is proprietary.
   - **Azure (3.5):** Kafka endpoint and Delta, but no Sparkplug.
   - **AWS (3.5):** Iceberg and PostgreSQL, but Kinesis is proprietary and there is no Sparkplug.

## Result: GCP, Narrowly

**GCP wins at 3.95 against Azure's 3.83.** It wins on the two highest-weighted criteria, which are also the ones this case study is *about*:
- plant autonomy with real edge HA
- the industrial protocol ecosystem, including the only native Sparkplug B

It also leads on analytics and ML fit. Azure is a close and credible second. AWS is a clear third, held down by the edge-HA gap on the two criteria where the edge matters most.

## Sensitivity: When Does the Answer Change?

| Scenario | Azure | AWS | GCP | Winner |
|---|---|---|---|---|
| Primary (as above) | 3.83 | 3.34 | **3.95** | GCP |
| Original provisional weights, **without** the genealogy criterion | 3.70 | 3.33 | **4.00** | GCP |
| Operations/skills weight +10 points (others scaled down) | 3.85 | 3.26 | **3.86** | GCP (essentially tied) |
| GCP's OT/edge score lowered to Azure's (4) | 3.83 | 3.34 | **3.84** | GCP (essentially tied) |
| GCP's operations score lowered to AWS's (2.5) | 3.83 | 3.34 | **3.88** | GCP |
| Azure's OT/edge raised to 4.5 (if the 72-hour ceiling were lifted) | 3.94 | 3.34 | **3.95** | GCP (essentially tied) |
| **Genealogy weight raised to 20%** | **3.96** | 3.36 | 3.90 | **Azure** |

These results mean three things:

- **The refinement did not create the result.** GCP wins by a wider margin *without* the added genealogy criterion (4.00 against 3.70). Adding it narrows the gap.
- **The decision is close, and it is mostly a trade between edge fit and genealogy/operations fit.** Several plausible re-scorings produce a statistical tie. The only single change that **flips** the result is treating genealogy integrity as twice as important as driver 3's rank (3rd of 5 drivers) supports.
- **So the conditions attached to the decision matter as much as the decision itself.** [ADR-024](../adr/ADR-024-cloud-platform-selection.md) makes GCP's two weakest areas, genealogy integrity and edge operations, explicit workstreams with owners rather than footnotes.

## What the Other Platforms Do Better (named, not hidden)

- **Azure** has the only **engine-enforced** genealogy immutability. It also has the simplest edge operating model (one vendor, one management plane in Arc), and a single analytics platform (Fabric). It also has the least new identity work, since Kestrel already runs Entra ID (other tracks federate to it cleanly, so this was not weighted). If Kestrel's OEM customers begin **auditing** genealogy immutability at the database layer, Azure's position improves materially.
- **AWS** has the best **native lane semantics** (stream manager priorities and TTL, with almost no custom outbox code), per-node X.509 device identity exactly as Step 5 specified, the strongest event-time stream processing (Flink), and the lowest directional edge cost. If Greengrass gains native HA, or an integrator offers a supported HA appliance, AWS's two weakest scores would rise.
- **GCP's own weaknesses**, which remain true after it wins:
  - three edge vendors
  - the most Kestrel-built edge code, since the entire outbox is custom
  - MCe's roughly 10K-tag instance limit and licence stacking
  - genealogy immutability no stronger than AWS's

## What This Matrix Deliberately Does Not Resolve

- **Dollar costs** are Step 12's job. Criterion 4 is directional. If Step 12 shows GCP's edge licence stack (GDC per vCPU + MCe + broker) is materially more expensive than Azure's per-node IoT Operations fee, ADR-024's review trigger applies.
- **Rollout sequencing** against the December 2026 and July 2027 shutdown windows and the insurer deadline is for Steps 10–11.
