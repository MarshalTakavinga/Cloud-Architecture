### ADR-030: Private-cloud compute for LinkEngine's message-subscriber logic

**Context:**
ADR-002 decided LinkEngine becomes an event-driven integration service — platform-neutral. Something has to run the code that subscribes to each message category, writes results into the primary database, and archives the raw payload to object-equivalent storage — the same starting question ADR-008 (Azure), ADR-015 (AWS), and ADR-022 (GCP) each answered for their platform. None of the serverless function products those platforms used (Azure Functions, Lambda, Cloud Run functions) has a private-cloud equivalent — VCF has no fully-managed, pay-per-invocation function-hosting primitive at all.

**Options considered:**
- Run the subscriber logic on the existing Citrix/CareLink PM VM tier, as a background Windows service
- A fixed pool of dedicated VMs running the subscriber logic as Windows or Linux services, sized for peak load
- VMware Tanzu (Tanzu Kubernetes Grid, VCF-integrated), running the four subscriber workloads as containerized deployments, autoscaled by KEDA against message-queue depth

**Decision:** VMware Tanzu, running one containerized deployment per message category, scaled by KEDA reacting to queue depth on the messaging platform (ADR-033).

**Rationale:**
Running this on the Citrix VM tier is rejected for the identical reason ADR-008/ADR-015/ADR-022 rejected the equivalent tier on every other platform: that tier is sized and scaled around interactive clinical session load, a completely different pattern from message-processing load. A fixed pool of dedicated VMs would work and would be the operationally simplest private-cloud option, but it reproduces the same "fixed capacity sized for the wrong load shape" problem in a new form — a VM pool sized for average load can't absorb a post-outage backlog spike without either being oversized every other hour of the day or falling behind during exactly the periods (a backlog after an incident) when reliability matters most. **Tanzu is chosen as VCF's own native path to the property every sibling platform got for free from a fully-managed function service: container-level granularity and event-driven autoscaling.** This is a genuine, worth-naming structural difference in *how* private cloud gets there: Cloud Run functions, Azure Functions, and Lambda are fully-managed primitives with no cluster for Meridian to operate at all; getting the equivalent elasticity here means standing up and operating a real Kubernetes platform. That's the same staffing tension ADR-002 raised generically about Kubernetes and full microservices — accepted here specifically because Tanzu's scope in this design stays narrow (four small subscriber workloads, not a general microservices platform), and because VCF bundles Tanzu's control-plane lifecycle management, which lowers the operational bar meaningfully below a from-scratch self-managed Kubernetes cluster.

**Trade-off:**
This is a second operationally distinct compute platform in the private-cloud environment (vSphere VMs for Citrix and SQL Server, Tanzu/Kubernetes for LinkEngine and, per ADR-032, the Portal) that the 16-person team must learn to run — the same category of trade-off named for the function platforms on every sibling ADR, but with meaningfully more real operational surface here: Tanzu is infrastructure Meridian operates directly (control-plane upgrades, worker node pool capacity, cluster HA), not a fully-managed abstraction the hyperscaler keeps invisible. If the team's Kubernetes comfort level doesn't materialize by go-live, the honest fallback is the fixed-VM-pool option above, accepting worse elasticity in exchange for zero new platform to operate — named here as a real fallback, not hidden as an afterthought.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Platform | VMware Tanzu Kubernetes Grid, one shared cluster serving both LinkEngine (this ADR) and the Portal (ADR-032) | Reusing one cluster across both workloads, rather than standing up a second, is a deliberate efficiency — the identical "don't duplicate platform investment" reasoning used to size ADR-026's Workload Domain, and a real advantage of consolidating both of Meridian's owned/refactored applications onto the same new platform layer |
| Cluster topology | 3 control-plane nodes, 6 worker nodes (day one), spread across ESXi hosts via anti-affinity | Kubernetes' own standard HA control-plane count; worker count sized for LinkEngine's four subscriber deployments plus the Portal's deployments (ADR-032) with headroom |
| Workload structure | 4 containerized Deployments (lab results, imaging, e-prescribing, appointment events), one per message-queue subscription | Direct parity with every sibling ADR's "one function per message category" |
| Autoscaling | KEDA (Kubernetes Event-Driven Autoscaling), scaling trigger = queue depth on the corresponding RabbitMQ queue (ADR-033) | The private-cloud analog to Cloud Run functions/Lambda/Azure Functions scaling on trigger backlog — KEDA is the open-source, Kubernetes-native way to get event-driven (not just CPU-based) autoscaling |
| Min / max replicas | Min 1, max 20 per Deployment | Direct parity with ADR-008/ADR-015/ADR-022's 1-min/20-max figures — min 1 avoids cold-start latency on clinically time-sensitive categories (lab results, e-prescribing); max 20 gives backlog-catch-up headroom |
| Resource requests/limits | 512 MiB memory, 0.5 vCPU per pod (starting point) | Mirrors the sibling ADRs' 512 MiB starting point — the subscriber workload is I/O-bound (parse a message, write to the database, archive to storage, acknowledge), not compute-bound |
| Network placement | Dedicated Integration Tier-1 segment (ADR-029, 10.50.0.0/16) | Same trust-boundary isolation reasoning as ADR-022/ADR-015/ADR-008 — this is the one compute tier reached by externally-triggered partner traffic (LabCorp, Quest, PACS, Surescripts via client certificate/API key), not a Meridian-authenticated user or staff member |
| Identity | A dedicated Kubernetes service account per Deployment, scoped via NSX Distributed Firewall rules to only the database VM (ADR-028) and its own message queue (ADR-033) | Same least-privilege discipline as every sibling ADR's per-function identity — no shared, over-privileged identity across all four workloads |

This sizing is a directional starting point, the same discipline every sizing ADR in this case study applies — there's no per-message-processing telemetry from the current on-prem LinkEngine to validate concurrency assumptions against. Cost for this configuration (Tanzu licensing, worker node hardware allocation shared with ADR-032) is deliberately not estimated here and stays with Step 13.

See [`../docs/application-architecture-private-cloud.md`](../docs/application-architecture-private-cloud.md) §4 for the full hosting narrative. No detail diagram exists yet for this ADR — hand-drawn diagrams are added incrementally and checked against this document once available.
