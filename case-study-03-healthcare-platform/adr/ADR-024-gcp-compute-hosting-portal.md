### ADR-024: GCP compute hosting model for MeridianConnect Portal

**Context:**
ADR-002 already decided the Portal is Refactor — Meridian-owned code, redesigned as a small number of bounded, event-driven services under the Strangler Fig approach, with Zero Trust applied throughout — platform-neutral. The question this ADR answers, mirroring ADR-010 for Azure and ADR-017 for AWS, is narrower: which specific GCP compute service actually runs the refactored Portal.

**Options considered:**
- Google Cloud Run (fully managed serverless containers, no cluster to patch)
- Google Kubernetes Engine (GKE)
- Google Compute Engine, in a Managed Instance Group behind a load balancer

**Decision:** Google Cloud Run, behind a Serverless Network Endpoint Group (NEG) reached through a global external Application Load Balancer, with Cloud CDN and Cloud Armor attached.

**Rationale:**
ADR-002 already ruled out full microservices decomposition on staffing grounds — no current Kubernetes/distributed-systems operating experience on a 16-person team — the identical argument that rules out GKE here, the same logic ADR-010/ADR-017 applied to AKS/EKS. Compute Engine in a Managed Instance Group would work, but it reintroduces exactly the patching/capacity-management burden this migration is trying to reduce, for a workload (one refactored web application, conventional scaling profile) that doesn't need VM-level control. **Here the reasoning genuinely diverges from ADR-010/ADR-017, not just the service name.** Azure's Container Apps and AWS's App Runner were both rejected specifically for being newer, less battle-tested products with weaker private-VPC-connectivity track records than the sibling platforms' mature container-orchestration services (AKS, ECS/Fargate). Cloud Run does not carry that same liability on GCP: it has been Google's flagship serverless application-hosting product since general availability in 2019 — older and more heavily used in production than either Container Apps or App Runner — and its VPC connectivity (Direct VPC egress) is a mature, default-path feature, not a recent bolt-on. On GCP, the simplest option and the most proven option are the same option, which is not true on Azure or AWS — a genuine, worth-naming platform difference rather than a mirrored conclusion reached by a different route.

**Trade-off:**
Cloud Run's per-request/per-instance pricing model costs more per unit of sustained compute than a comparable Compute Engine reserved fleet would, and is less flexible than GKE if the Portal is ever decomposed into many independently-scaled services with fine-grained per-service policies — the same trade-off ADR-010/ADR-017 named for their respective platforms. Accepted for the identical reason: the Portal's current scope doesn't need that operational surface. Revisit if the Portal is later split into multiple bounded services under continued Strangler Fig work.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Platform | Cloud Run (fully managed) | Decided above — removes the patching/capacity-management burden a self-managed Compute Engine fleet would carry |
| CPU / memory (starting point) | 1 vCPU / 2 GiB per instance | Direct parity with ADR-017's 1 vCPU / 2 GB Fargate starting point and ADR-010's 2 vCPU / 8 GB (right-sized down, same reasoning: a web/API tier that isn't itself compute- or memory-heavy) |
| Runtime | Linux containers | Matches the container-based runtime already established for Azure/AWS — an application-layer decision outside this infrastructure ADR's scope |
| Min instances | 3 | Direct parity with ADR-010/ADR-017's autoscale floor of 3 — unlike Compute Engine or GKE, Cloud Run's min-instances setting isn't a zone-coverage mechanism the way "1 per AZ" was on AWS/Azure (Cloud Run's regional service is inherently multi-zone within the region, mirroring the subnet-regionality point in ADR-021); the floor here exists instead to avoid cold-start latency on the first request after idle, kept at 3 for direct comparability with the sibling ADRs' numbers rather than a platform-forced minimum |
| Max instances | 10 | Direct parity with ADR-010/ADR-017's 10-instance ceiling — see the load estimate below, reused unchanged since the demand-side numbers are platform-independent |
| Load balancing / public entry | Global external Application Load Balancer, with Cloud CDN and Cloud Armor (WAF + DDoS protection) attached, routing to Cloud Run via a Serverless NEG | Direct analog to ADR-017's CloudFront + WAF + VPC-origin-to-internal-ALB path and ADR-010's Front Door Premium + WAF path — the Serverless NEG is GCP's mechanism for a load balancer to reach a Cloud Run service without the service needing a public IP of its own |
| VPC integration (private data path) | Direct VPC egress into `subnet-app`, Application VPC — shared with Apigee's runtime and Citrix/CareLink PM, not a dedicated subnet of its own (see `gcp-implementation.md` §4.1) | What lets the Portal reach Cloud SQL privately instead of over a public connection string — see ADR-021 for why this is one regional subnet, not one per zone the way ADR-017's AWS equivalent needed. LinkEngine's functions sit in their own separate Integration VPC, not here — see ADR-022 |

**Where the 3-10 range comes from.** Identical to ADR-010/ADR-017, reused unchanged since these are demand-side figures, not platform-specific ones: no captured concurrent-user or request-rate figure exists for the Portal, only the same ~410,000 active-patient population and 8-12 second peak-load-time symptom used throughout this case study, producing the same ~200 concurrent sessions / 20-30 requests-per-second-at-peak planning estimate. A single 1 vCPU / 2 GiB Cloud Run instance comfortably handles that request volume for a lightweight web/API workload — the 3-10 range is sized for headroom and comparability, not because peak load itself demands 10 instances.

This estimate should be validated against real Cloud Monitoring telemetry in the first 90 days after launch, the same "provisional starting point" discipline applied throughout this case study. Cost for this configuration is deliberately not estimated here and stays with Step 13.

See [`../docs/application-architecture-gcp.md`](../docs/application-architecture-gcp.md) §2 for the full hosting narrative, and [`../diagrams/portal-hosting-architecture-gcp.png`](../diagrams/portal-hosting-architecture-gcp.png) for the detailed public entry, protection, and private data path diagram matching this ADR's Proposed Configuration. Hand-reproduced, checked against this ADR across two review rounds: the first submission sequenced the public entry flow as LB → Serverless NEG → Cloud CDN → Cloud Armor → Cloud Run, putting the WAF/DDoS layer after caching and backend routing instead of before — corrected to LB → Cloud Armor → Cloud CDN → Serverless NEG → Cloud Run, matching how these components actually evaluate a request — and fixed a References-panel citation pointing at `gcp-implementation.md` §2 (which is CareLink PM compute, unrelated) instead of `application-architecture-gcp.md` §2.
