### ADR-017: AWS compute hosting model for MeridianConnect Portal

**Context:**
ADR-002 already decided the Portal is Refactor, not Rehost — Meridian-owned code, redesigned as a small number of bounded, event-driven services under the Strangler Fig approach, with Zero Trust applied throughout. That's a style decision, not an infrastructure one, and it's platform-neutral. The question this ADR answers, mirroring ADR-010 for Azure, is narrower: which specific AWS compute service actually runs the refactored Portal.

**Options considered:**
- Amazon ECS on AWS Fargate (serverless containers, no cluster to patch)
- Amazon Elastic Kubernetes Service (EKS)
- AWS App Runner (fully-managed, source-to-URL container service)
- Amazon S3 + CloudFront (static frontend) + a separate serverless API backend

**Decision:** Amazon ECS on AWS Fargate, behind an internal Application Load Balancer, fronted by Amazon CloudFront.

**Rationale:**
ADR-002 already ruled out full microservices decomposition on the grounds that a 16-person infrastructure team with no current Kubernetes/distributed-systems operating experience shouldn't take on a distributed-operations problem it isn't staffed for — that argument applies directly to EKS specifically, not just to the general microservices question, the same logic ADR-010 applied to AKS. AWS App Runner would remove even more operational surface than Fargate (no task definitions, no cluster concepts to reason about), but it's a newer service with a smaller production track record and materially less granular VPC networking control than ECS/Fargate — specifically, App Runner's private VPC connectivity for reaching a database privately is a later, less battle-tested addition to the service than Fargate's native VPC-attached ENIs, and the Portal needs reliable, private, always-on connectivity to RDS Custom for SQL Server, not just outbound internet access. This mirrors ADR-010's rejection of Azure Container Apps: the newer, lighter-weight PaaS option solves a problem (rapid iteration on many small event-driven services) the Portal doesn't have — it's one refactored web application with a conventional scaling profile, not a fleet of independently-versioned microservices. S3 + CloudFront with a serverless API backend is a strong fit for a purely static frontend, but the Portal needs direct, private, VPC-integrated connectivity to the primary database for scheduling/billing data, not just static content — exactly what ECS Fargate's VPC-attached tasks provide natively, mirroring ADR-010's rejection of Azure Static Web Apps for the identical reason.

**Trade-off:**
ECS Fargate costs more per unit of compute than a comparable EC2 Reserved Instance fleet would, and is less flexible than EKS if the Portal ever needs to decompose into many independently-scaled services with fine-grained per-service autoscaling policies. Accepted because the VPC-private connectivity and zone-redundant HA this design's Zero Trust posture requires are available on Fargate without the cluster-operations burden EKS would add, and the Portal's current scope (one refactored web application, not a services mesh) doesn't need EKS's added operational surface. Revisit if the Portal is later split into multiple bounded services under continued Strangler Fig work — the identical revisit condition ADR-010 named for AKS/ACA. Cost is a Step 13 concern, not decided here.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Launch type | AWS Fargate (serverless, no EC2 instances to manage) | Decided above — removes the patching/capacity-management burden a self-managed EC2 launch type on ECS would carry |
| Task size (starting point) | 1 vCPU / 2 GB per task | A moderate starting size for a web/API tier that isn't itself compute- or memory-heavy — direct parity with ADR-010's P1v3 (2 vCPU / 8 GB) starting point, right-sized down slightly since Fargate task pricing is granular per-vCPU/GB rather than a fixed instance SKU |
| Runtime | Linux containers | Matches the Linux, container-based runtime already established for Azure — an application-layer decision outside this infrastructure ADR's scope, carried forward unchanged |
| Autoscale floor | 3 tasks (1 per Availability Zone, across the 3 AZs used elsewhere in this design) | Same availability-floor reasoning as ADR-010: this is a zone-coverage requirement, not a load minimum — going below 3 would silently drop AZ coverage regardless of traffic |
| Autoscale ceiling | 10 tasks | Direct parity with ADR-010's 10-instance ceiling — see the load estimate below, reused unchanged from ADR-010 since the demand-side numbers are platform-independent |
| Load balancing | Internal Application Load Balancer, VPC-private | Fargate tasks sit behind an ALB with no public IP; the ALB itself is internal (private subnets only) |
| Public entry point | Amazon CloudFront, with AWS WAF attached | Direct parity with ADR-010's Azure Front Door Premium + WAF — CloudFront terminates public traffic and reaches the internal ALB over a VPC origin (AWS's equivalent of Front Door's Private Link origin, avoiding a public path to the ALB) |
| VPC integration | Fargate tasks run in `subnet-ecs-portal-az1/az2/az3` (10.20.2.0/26, 10.20.2.64/26, 10.20.2.128/26), Application VPC private subnets, one per AZ matching the 3-AZ autoscale floor | Direct parity with ADR-010's `snet-appsvc` — this is what lets the Portal reach the database privately instead of over a public connection string. Three subnets, not one, since an AWS subnet is scoped to a single Availability Zone — see `aws-implementation.md` §4.1 |

**Where the 3-10 range comes from.** Identical to ADR-010, reused unchanged since these are demand-side figures, not platform-specific ones: no captured concurrent-user or request-rate figure exists for the Portal in `requirements.md` or `current-state.md`, only adjacent population data (~410,000 active patients in the last 24 months) and a documented failure symptom (8-12 second page loads during Monday-morning flu-season peaks).

- Planning assumption: ~3% of active patients engage with the portal on a peak day (~12,300 users)
- Planning assumption: ~25% of peak-day users concentrate in the single busiest hour (~3,075 users in that hour)
- Planning assumption: ~4-minute average session length → roughly 200 concurrent sessions at peak, translating to a sustained request rate on the order of 20-30 requests/second with higher bursts
- A single 1 vCPU / 2 GB Fargate task comfortably handles that request volume for a lightweight web/API workload — meaning the 3-10 task range here, exactly as in ADR-010, is sized for zone redundancy and growth headroom, not because the estimated peak load itself requires 10 tasks

This estimate should be validated against real CloudWatch/X-Ray telemetry in the first 90 days after launch, the same "provisional starting point, not a final number" discipline applied throughout this case study. Cost for this configuration is deliberately not estimated here and stays with Step 13.

See [`../docs/application-architecture-aws.md`](../docs/application-architecture-aws.md) §2 for the full hosting narrative, [`../diagrams/portal-architecture-aws.png`](../diagrams/portal-architecture-aws.png) for the component view, and [`../diagrams/portal-hosting-architecture-aws.png`](../diagrams/portal-hosting-architecture-aws.png) for the detailed sizing/hosting diagram matching this ADR's Proposed Configuration (CloudFront/WAF/VPC-origin entry path, per-AZ Fargate subnets, and private-path data access).
