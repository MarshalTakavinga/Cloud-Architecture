### ADR-021: GCP compute hosting for customer-facing regional services

**Context:**
ADR-001 decided Storefront & Catalog and Checkout & Payment are Rearchitect, Cart is Refactor. ADR-002 decided all three run per active region (US, EU, APAC): Storefront & Catalog active-active for reads, Cart and Checkout & Payment regional-primary. `requirements.md` §3 sets the same elasticity target this compute layer has to hit on every platform track: sustain a 25x baseline throughput ramp within 5 minutes of demand onset, without manual intervention. Unlike the AWS track (ADR-013), this platform carries no in-place migration story worth naming  `current-state.md` §1 names Solstice's production fleet as EC2, not GCP, so there is no existing GCP workload to build familiarity from and no US-region cutover risk to carry forward; all three regions are equally greenfield here, a genuine, worth-stating difference from the AWS track rather than an assumed equivalence.

**Options considered:**
- Compute Engine Managed Instance Groups (MIGs), autoscaled  the direct GCP analog of the current EC2 Auto Scaling Group.
- Google Kubernetes Engine (GKE, Autopilot or Standard), with Horizontal Pod Autoscaling.
- App Engine (flexible environment).
- Cloud Run, fully managed, with concurrency- and CPU-utilization-based autoscaling.

**Decision:**
Cloud Run. One Cloud Run service (Storefront & Catalog and Cart) runs per active region. A **second, separate** Cloud Run service, reached through its own Serverless VPC Access connector into a dedicated subnet, runs Checkout & Payment only, per active region.

**Rationale:**
Compute Engine MIGs are rejected for the same structural reason the current-state EC2 ASG doesn't work (`current-state.md` §2): autoscaling a VM fleet doesn't fix an in-memory-cache cold start or a shared-connection-pool coupling problem, it just moves the same defect onto a different VM product  the fix has to remove the coupling, not resize around it. App Engine flexible environment is rejected because its scale-out is itself VM-based underneath, carrying comparable multi-minute instance provisioning time that doesn't reliably clear a single-digit-minute, 25x ramp. GKE is rejected for the identical staffing reason ADR-005 rejected AKS and ADR-013 rejected EKS: it hands Solstice's 22-person engineering org a Kubernetes control plane  node pools, upgrades, cluster networking  to operate, for a workload ADR-002 already scoped to "a small number of independently-scalable services," not a service-mesh-heavy operating model. Cloud Run removes the server fleet from the equation entirely: it is a fully managed, serverless container platform with per-request autoscaling, sub-few-second cold starts for a well-built container image, and no cluster or node pool to size or patch. Paired with removing the in-memory catalog cache from the request path (Section 2), a cache miss  not a cold container  is the only path that touches the database, the same root-cause fix Azure's ADR-005 (Container Apps) and AWS's ADR-013 (Fargate) reached independently, arrived at a third time here because the underlying defect is identical regardless of platform.

Checkout & Payment gets its own dedicated Cloud Run service and Serverless VPC Access connector for the same PCI-isolation reason ADR-005 and ADR-013 gave it on the other two tracks: the isolated network segment ADR-001/ADR-002 require has to be a structural network property, not a policy statement. On GCP this is implemented slightly differently in kind, worth naming rather than glossing over as identical to a dedicated-subnet-only model: Checkout & Payment's Cloud Run service routes through its own dedicated subnet via a dedicated Serverless VPC Access connector, and sits inside its own VPC Service Controls perimeter  a GCP-native mechanism that restricts which GCP-managed resources (Cloud SQL, Secret Manager, Cloud Storage) the checkout path can reach at the API/control-plane level, on top of the network-level subnet isolation AWS and Azure rely on alone.

**Trade-off:**
Cloud Run's per-request billing model is a different cost shape than ECS Fargate's or Container Apps' provisioned-capacity model  accepted for the same "pay for the platform doing the operational work" reasoning the other two tracks accepted their own compute premium, but worth naming precisely rather than assuming it nets out the same: without a configured minimum instance count, Cloud Run's container instances can scale to zero between requests, and the very first requests after a scale-to-zero event carry a real (if small) cold-start cost  a genuine risk during the opening seconds of a flash-sale ramp specifically. This design accepts a non-zero minimum-instance floor (see Proposed Configuration) year-round specifically to avoid that risk during the ramps `requirements.md` §1 names, trading away part of Cloud Run's scale-to-zero cost advantage for the same fast-reaction guarantee KEDA and Application Auto Scaling target-tracking provide on the other tracks.

Unlike ADR-013's honestly-named US migration risk, this track has no equivalent asymmetry  all three regions provision cleanly from a greenfield state, a genuine (if minor) simplification for Step 11's rollout planning worth carrying into Step 9's comparison rather than treated as a wash.

**Proposed Configuration:**

| Setting | Storefront & Catalog / Cart service | Checkout & Payment service |
| --- | --- | --- |
| Platform | Cloud Run (fully managed) | Cloud Run (fully managed) |
| Minimum instances (floor) | 4/region | 2/region |
| Maximum instances (ceiling, 25x event) | ~80/region | ~30/region |
| CPU / memory per instance | 1 vCPU / 2 GiB, CPU always allocated | 0.5 vCPU / 1 GiB, CPU always allocated  PCI traffic volume is a fraction of storefront browse traffic |
| Concurrency | ~40 concurrent requests/instance, target-based autoscaling | ~20 concurrent requests/instance, given longer-running checkout transactions |
| Networking | Serverless VPC Access connector into `subnet-storefront-cart` | Dedicated Serverless VPC Access connector into `subnet-checkout`, own VPC Service Controls perimeter |
| Regional split assumption | Directional only  mirrors ADR-005/ADR-013's assumption; revisited once real post-launch regional traffic data exists (Step 11) | Same directional split |

**Status:** Approved

---

See [diagram](../diagrams/gcp-compute-customer-facing-services.png).
