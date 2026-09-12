### ADR-013: AWS compute hosting for customer-facing regional services

**Context:**
ADR-001 decided Storefront & Catalog and Checkout & Payment are Rearchitect, Cart is Refactor. ADR-002 decided all three run per active region (US, EU, APAC): Storefront & Catalog active-active for reads, Cart and Checkout & Payment regional-primary. `requirements.md` §3 sets the same elasticity target this compute layer has to hit on every platform track: sustain a 25x baseline throughput ramp within 5 minutes of demand onset, without manual intervention. This decision carries a genuinely different starting point on AWS than on Azure, worth naming plainly: Solstice already runs this exact workload on AWS today. `current-state.md` §1 names the current fleet directly  a fixed Auto Scaling Group of 12–18 `m5.2xlarge` EC2 instances behind an Application Load Balancer  and `current-state.md` §2 already proved, in production, why simply retuning that fleet doesn't clear the bar: a 3–4 minute per-instance cold start (dependency-injection bootstrap, in-memory catalog cache warm, Redis connection-pool establishment) is too slow to react inside a single-digit-minute ramp, and during the November 2024 outage the ASG's response  adding instances that each opened their own database connection pool against the same single RDS instance  made the incident worse, not better. Whatever AWS compute is chosen here has to fix the actual defect, not just move the same defect onto newer infrastructure.

**Options considered:**
- Keep the existing EC2 Auto Scaling Group, resized and retuned (larger instance types, pre-warmed pools, faster AMIs).
- Amazon EKS (Kubernetes), with KEDA-driven Horizontal Pod Autoscaler and Cluster Autoscaler for node-level scale-out.
- AWS Elastic Beanstalk, a managed wrapper around an EC2 Auto Scaling Group.
- Amazon ECS on AWS Fargate, with Application Auto Scaling target-tracking on ALB request count.

**Decision:**
Amazon ECS on AWS Fargate. One ECS service (Storefront & Catalog and Cart) runs per active region on Fargate. A **second, separate** ECS service, in its own dedicated subnet, runs Checkout & Payment only, per active region.

**Rationale:**
Retuning the existing EC2 ASG is rejected for a reason this case study doesn't have to argue hypothetically  `current-state.md` §2 already demonstrated it empirically in production. The defect isn't instance size or ASG tuning; it's that every new instance still bootstraps a heavy in-memory cache and opens its own connection pool against a single, unpartitioned database, an architectural coupling problem no ASG parameter fixes. Elastic Beanstalk is rejected because underneath its managed console it still deploys to an EC2 Auto Scaling Group  it changes who configures the ASG, not the fundamental instance-boot and connection-pool problem. EKS is rejected for the identical staffing reason ADR-005 rejected AKS on the Azure track: it hands Solstice's 22-person engineering org a Kubernetes control plane to operate  node pool lifecycle, CNI networking, cluster upgrades  for a workload ADR-002 already scoped to "a small number of independently-scalable services," not a service-mesh-heavy operating model. Fargate removes the EC2 fleet from the equation entirely: containers start in low single-digit seconds with no OS to boot and no AMI to warm, and Application Auto Scaling's target-tracking policies react continuously to ALB `RequestCountPerTarget` rather than the coarser, alarm-polling cadence the current ASG uses. Paired with removing the in-memory catalog cache from the request path (see Section 1 of the equivalent per-service detail in this document's Section 2), there's no warm-up penalty to scaling out  the same root-cause fix Azure's ADR-005 applied via Container Apps, reached independently here because the underlying defect is identical regardless of platform.

Checkout & Payment gets its own dedicated ECS service and subnet for the same PCI-isolation reason ADR-005 gave it on Azure: the isolated network segment ADR-001/ADR-002 require has to be a structural network property, not a policy statement, and a shared Fargate service would put Checkout & Payment's tasks on the same ENIs and subnet as Storefront & Catalog's general browse traffic.

**Trade-off:**
Fargate carries a higher per-vCPU/per-GB cost than equivalently-sized EC2 Reserved or Spot capacity  the same "pay for the platform doing the operational work" trade-off Azure accepted choosing Container Apps over raw VM scale sets. Accepted for the identical reason: engineering time not spent patching and right-sizing EC2 AMIs is worth more to a 22-person team than the per-unit compute delta, and Savings Plans can recover part of that premium once real utilization data exists (Step 12/13). Running two ECS services per active region instead of one shared service means a higher combined minimum footprint to provision and monitor  the same trade-off, and the same acceptance, ADR-005 made on Azure.

One trade-off specific to this platform track, stated honestly rather than glossed over: unlike EU and APAC, the US region isn't a greenfield footprint  Solstice already operates in `us-east-1` today. This ADR still specifies a fresh ECS deployment there rather than incrementally patching the existing EC2 fleet in place, because the actual defect (shared connection pools, in-memory cache warm-up) lives in the application's current deployment shape, not its instance type; a like-for-like lift onto Fargate without also removing that coupling would reproduce the same failure mode on newer infrastructure. That means the US region carries a real cutover/migration step the other two platform tracks' US regions don't (they're greenfield everywhere)  a genuine AWS-track-specific planning input for Step 11.

**Proposed Configuration:**

| Setting | Storefront & Catalog / Cart service | Checkout & Payment service |
| --- | --- | --- |
| Launch type | AWS Fargate | AWS Fargate |
| Task count (floor) | Storefront & Catalog: 4/region; Cart: 2/region | 2/region |
| Task count (ceiling, 25x event) | Storefront & Catalog: ~80/region; Cart: ~40/region | ~30/region |
| Task sizing | 1 vCPU / 2 GB | 0.5 vCPU / 1 GB  PCI traffic volume is a fraction of storefront browse traffic |
| Scaling policy | Application Auto Scaling, target tracking on ALB `RequestCountPerTarget` (~40/target), continuous evaluation | Same target-tracking mechanism, lower target (~20/target) given longer-running checkout transactions |
| Regional split assumption | Directional only  mirrors ADR-005's assumption; revisited once real post-launch regional traffic data exists (Step 11) | Same directional split |

**Status:** Approved

---

See [diagram](../diagrams/aws-compute-customer-facing-services.png).
