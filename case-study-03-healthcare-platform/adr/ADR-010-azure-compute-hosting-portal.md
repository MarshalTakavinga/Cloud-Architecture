### ADR-010: Azure compute hosting model for MeridianConnect Portal

**Context:**
ADR-002 already decided the Portal is Refactor, not Rehost — it's Meridian-owned code, redesigned as a small number of bounded, event-driven services under the Strangler Fig approach, with Zero Trust applied throughout. That's a style decision, not an infrastructure one. The question this ADR answers is narrower: which specific Azure compute service actually runs the refactored Portal.

**Options considered:**
- Azure App Service (PaaS, Linux, container-based)
- Azure Kubernetes Service (AKS)
- Azure Container Apps (ACA)
- Azure Static Web Apps (frontend) + a separate API backend

**Decision:** Azure App Service, Premium v3, Linux.

**Rationale:**
ADR-002 already ruled out full microservices decomposition on the grounds that a 16-person infrastructure team with no current Kubernetes/distributed-systems operating experience shouldn't take on a distributed-operations problem it isn't staffed for — that argument applies directly to AKS specifically, not just to the general microservices question. Azure Container Apps reduces some of AKS's operational burden (no cluster to patch), but it's a newer service with a smaller production track record than App Service, and its strengths — per-revision traffic splitting, KEDA-based event-driven scaling for many small services — solve a problem the Portal doesn't have: it's one web application with a clear, conventional scaling profile (CPU/memory/request-queue), not a fleet of independently-versioned microservices. Static Web Apps is a strong fit for a purely static frontend backed by a serverless API, but the Portal needs direct, private, VNet-integrated connectivity to Azure SQL Managed Instance (patient scheduling/billing data, not just static content) — that's exactly what App Service's regional VNet integration provides natively, and it's also why LinkEngine's event-driven backend (ADR-008) uses Azure Functions rather than folding the Portal itself into that model. App Service Premium v3 is the plan tier that supports both zone redundancy and regional VNet integration together — Standard does not.

**Trade-off:**
Premium v3 costs more than App Service Standard tier or a Consumption-based serverless option, and App Service in general is less flexible than AKS/ACA if the Portal ever needs to decompose into many independently-scaled services. Accepted because the VNet integration and zone-redundant HA this design's Zero Trust posture requires are available out of the box on Premium v3, and the Portal's current scope (one refactored web application, not a services mesh) doesn't need AKS/ACA's added operational surface. Revisit if the Portal is later split into multiple bounded services under continued Strangler Fig work. Cost is a Step 13 concern, not decided here.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Plan tier | Premium v3, Linux | Decided above — the tier that supports both zone redundancy and regional VNet integration |
| Instance size (starting point) | P1v3 (2 vCPU / 8 GB) | A moderate starting SKU for a web/API tier that isn't itself compute- or memory-heavy — see the load estimate below for why this is comfortably sized, with room to move to P2v3/P3v3 if real usage says otherwise |
| Runtime | Linux, container-based (already decided in `azure-implementation.md`) | Language/framework choice is an application decision outside this infrastructure ADR's scope — not invented here |
| Autoscale floor | 3 instances (1 per Availability Zone) | This is an **availability** floor, not a load floor — Premium v3 zone redundancy requires at least one instance per zone to actually spread across all three; going below 3 would silently drop zone coverage regardless of traffic |
| Autoscale ceiling | 10 instances | Load-driven — see estimate below. Autoscale trigger stays CPU utilization + HTTP request queue length, as already stated in `application-architecture.md` |
| VNet integration | Regional VNet integration into `snet-appsvc` (10.20.2.0/24) | Already established in `azure-implementation.md` §4.1 — this is what lets App Service reach SQL MI over a private endpoint instead of a public connection string |

**Where the 3–10 range comes from.** Unlike CareLink PM's Citrix sessions, there's no captured concurrent-user or request-rate figure for the Portal in `requirements.md` or `current-state.md` — only adjacent population data (~410,000 active patients in the last 24 months) and a documented failure symptom (8–12 second page loads and rising self-scheduling abandonment during Monday-morning flu-season peaks). This is a real gap, more provisional than ADR-005's Citrix numbers, and worth being explicit about rather than papering over with false precision:

- Planning assumption: ~3% of active patients engage with the portal on a peak day (~12,300 users) — not a captured figure, a directional estimate
- Planning assumption: ~25% of peak-day users concentrate in the single busiest hour, mirroring the same Monday-morning pattern that drives the Citrix peak (~3,075 users in that hour)
- Planning assumption: ~4-minute average session length → roughly 200 concurrent sessions at any instant during peak hour, translating to a sustained request rate on the order of 20–30 requests/second with higher bursts
- A single P1v3 instance comfortably handles that request volume for a lightweight web/API workload — meaning the 3–10 instance range here is sized for zone redundancy and growth headroom (340% portal usage growth since 2020, the in-flight 9-clinic acquisition, seasonal spikes), not because the estimated peak load itself requires 10 instances

One more point worth making explicit: `current-state.md` frames the 8–12 second page-load problem as a symptom of the *entire* on-prem VMware cluster running at ~85% peak utilization — shared across CareLink PM, the portal, and everything else — not evidence that the portal specifically needs more compute than this estimate suggests. Moving to a dedicated, autoscaled App Service plan with its own dedicated SQL MI capacity (not a shared, contended cluster) plausibly fixes the root cause on its own. This estimate should be validated against real Application Insights telemetry in the first 90 days after launch, and the autoscale thresholds adjusted from there — the same "provisional starting point, not a final number" discipline applied to ADR-005 and ADR-006. Cost for this configuration is deliberately not estimated here and stays with Step 13.

See [`../diagrams/portal-hosting-architecture.png`](../diagrams/portal-hosting-architecture.png) for the full hosting diagram, including Front Door as the actual public entry point and App Service's Private Link-only access restriction.
