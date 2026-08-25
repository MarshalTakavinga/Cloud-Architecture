### ADR-005: Azure compute hosting for customer-facing regional services

**Context:**
ADR-001 decided Storefront & Catalog and Checkout & Payment are Rearchitect, Cart is Refactor. ADR-002 decided all three run per active region (US, EU, APAC): Storefront & Catalog active-active for reads, Cart and Checkout & Payment regional-primary. `requirements.md` §3 sets the elasticity target this compute layer has to hit: sustain a 25x baseline throughput ramp within 5 minutes of demand onset, without manual intervention  and §1 shows that's not a theoretical number, a flash sale has actually ramped traffic in as little as ~4 minutes. `current-state.md` §2 already showed why this is hard, not just a checkbox: SCE's Auto Scaling Group is technically "on" today, but a 3–4 minute per-instance cold start (dependency-injection bootstrap, in-memory catalog cache warm, Redis connection-pool establishment) makes it too slow to react inside that window, and during the November 2024 outage the ASG's response  adding instances that each opened their own database connection pool  made the incident worse, not better. Whatever Azure compute is chosen here has to genuinely clear the 5-minute bar, not just have "autoscaling" enabled on paper the way the current fleet does.

**Options considered:**
- Azure App Service (Premium v3, instance-count autoscale rules on CPU/memory/queue-length thresholds)  the default PaaS web-tier choice, and what Case Study 3 used for Meridian's Portal.
- Azure Kubernetes Service (AKS), with KEDA-driven Horizontal Pod Autoscaler and Cluster Autoscaler for node-level scale-out.
- Azure Container Apps  serverless containers on a managed Kubernetes/KEDA foundation, with HTTP-concurrency and queue-depth scaling rules and scale-to-zero for non-production environments.

**Decision:**
Azure Container Apps. One Container Apps Environment per active region hosts Storefront & Catalog and Cart. A **second, separate** Container Apps Environment per active region, injected into its own dedicated subnet, hosts Checkout & Payment only.

**Rationale:**
App Service is rejected as the primary choice here for the same reason it was the right choice for Case Study 3's Portal  traffic shape. Meridian's Portal traffic is comparatively steady; Solstice's is a named 20–25x spike inside single-digit minutes. App Service's autoscale evaluates on a polling interval and scales in whole-instance increments  meaningfully slower and coarser than a true flash-sale ramp needs. AKS is rejected not because it can't scale fast enough (KEDA plus Cluster Autoscaler genuinely can clear the 5-minute bar) but because it hands Solstice's 22-person engineering org a Kubernetes cluster to operate  node pool lifecycle, CNI networking, cluster upgrades, cluster-level security patching  for a workload ADR-002 already decided should be "a small number of independently-scalable services," not a service-mesh-heavy operating model the team isn't staffed to run. Container Apps gives KEDA-based scaling (the same scaling engine AKS would use) without the cluster underneath it to operate. It also directly addresses the actual root cause named in `current-state.md` §2: a lean, stateless container with no in-memory cache to warm and no local connection pool to establish starts in low single-digit seconds, not 3–4 minutes  see `application-architecture.md` for exactly how the in-memory-cache dependency is removed from the request path.

The second Container Apps Environment for Checkout & Payment is not redundancy for its own sake. Checkout & Payment's entire reason for existing as a separately Rearchitected component (ADR-001, ADR-002) is PCI scope reduction through an "isolated network segment." Azure Container Apps Environments are VNet-injected as a unit  every app inside one environment shares that environment's injected subnet. Sharing one environment between Storefront & Catalog and Checkout & Payment would make "isolated network segment" a policy statement, not a structural property. A second environment, injected into its own dedicated subnet with its own network security group, is what makes the isolation real at the network layer, not just at the code layer  see ADR-012 and the network addressing detail for the actual subnet plan.

**Trade-off:**
Container Apps is a comparatively newer Azure product than App Service, with a narrower built-in feature set (for example, less mature deployment-slot tooling) and a smaller operational track record. Running two environments per active region  six total across US, EU, and APAC  instead of one shared environment per region means more resources to provision, monitor, and carry minimum platform overhead on. Accepted because the PCI isolation this buys is worth more than the marginal simplicity of a single shared environment per region, and because minimum per-environment overhead is a small line item next to the cost-per-order target this design is chasing in aggregate.

**Proposed Configuration:**

| Setting | Storefront & Catalog / Cart environment | Checkout & Payment environment |
| --- | --- | --- |
| Environment count | 1 per active region (3 total) | 1 per active region (3 total) |
| Workload profile | Consumption + Dedicated (D4 general-purpose) mixed profile  Consumption absorbs the elastic spike, Dedicated holds a stable floor | Consumption + Dedicated (D2 general-purpose)  smaller floor, PCI traffic volume is a fraction of storefront browse traffic |
| Baseline replicas (floor) | Storefront & Catalog: 4/region; Cart: 2/region | 2/region |
| Peak replicas (ceiling, 25x event) | Storefront & Catalog: ~80/region; Cart: ~40/region | ~30/region |
| Scale rule | HTTP concurrent-request-based (target ~40 concurrent requests/replica), evaluated every 15 seconds | Same HTTP concurrency trigger, lower concurrency target (~20/replica) given longer-running checkout transactions |
| Regional split assumption | Directional only  US carries roughly half of total capacity today given the existing US/Canada customer base, EU and APAC roughly a quarter each; revisited once real post-launch regional traffic data exists (Step 12) | Same directional split |

**Status:** Approved
