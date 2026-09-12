### ADR-032: Private-cloud compute hosting model for MeridianConnect Portal

**Context:**
ADR-002 already decided the Portal is Refactor — Meridian-owned code, redesigned as a small number of bounded, event-driven services under the Strangler Fig approach, with Zero Trust applied throughout — platform-neutral. The question this ADR answers, mirroring ADR-010 (Azure), ADR-017 (AWS), and ADR-024 (GCP), is which private-cloud compute service actually runs it — and, separately, what sits in front of it, since VCF has no built-in equivalent to a hyperscaler's global CDN/WAF edge.

**Options considered:**
- VMware Tanzu (the same Tanzu Kubernetes Grid cluster already justified for LinkEngine in ADR-030), Portal deployed as containerized Deployments
- A fixed pool of dedicated VMs behind a load balancer
- Full microservices decomposition on a dedicated, larger Kubernetes footprint

**Decision:** VMware Tanzu (the shared cluster from ADR-030), Portal deployed as containerized Deployments behind the NSX Advanced Load Balancer, fronted by a third-party SaaS CDN/WAF placed in front of the colocation facilities' public IP space.

**Rationale:**
Full microservices decomposition is ruled out on the identical staffing grounds ADR-002 already established generically. A fixed VM pool would work, but it recreates the same elasticity mismatch every sibling Portal ADR (ADR-010/ADR-017/ADR-024) rejected for this specifically bursty, patient-facing traffic pattern (open-enrollment periods, a weather event driving a rescheduling surge) — and private cloud has no serverless container primitive of its own (no Cloud Run/App Runner/Container Apps equivalent) to reach for instead. The realistic way to get comparable event-driven, scale-on-demand behavior is the same Tanzu platform ADR-030 already justified for LinkEngine — reusing rather than duplicating that platform investment is a real efficiency specific to this track, not available to the hyperscaler designs, each of which stood up a separate function product and a separate container-hosting product. **A gap worth naming with the same directness this case study applies to every other platform's gaps**: none of VCF, NSX, or Tanzu includes a CDN or an internet-facing WAF/DDoS-scrubbing service comparable to Cloud Armor + Cloud CDN (GCP), CloudFront + WAF (AWS), or Front Door Premium + WAF (Azure) — those are edge/anycast capabilities inherent to a hyperscaler's global point-of-presence footprint, and a two-facility private-cloud deployment cannot replicate that footprint itself at any reasonable cost. The honest private-cloud answer is a third-party SaaS CDN/WAF product placed in front of the colocation facilities' public IP space — a deliberate, named external dependency, the same posture ADR-031 already took for patient identity.

**Trade-off:**
Two distinct external SaaS dependencies now sit at this platform's public edge (CIAM per ADR-031, CDN/WAF here) — the private-cloud track, despite keeping compute and data under Meridian's own physical control, is not actually more self-contained than the hyperscaler tracks at the perimeter. If anything, it now depends on more distinct external vendors in aggregate (the colocation operators, the CIAM vendor, the CDN/WAF vendor) than a single hyperscaler subscription requires. This should weigh into Step 10's vendor-count and vendor-risk comparison honestly, alongside the capability comparison, not be treated as a footnote.

**Status:** Proposed

---

**Proposed Configuration:**

| Setting | Proposed value | Rationale |
| --- | --- | --- |
| Platform | VMware Tanzu (shared cluster with ADR-030) | Decided above |
| CPU / memory (starting point) | 1 vCPU / 2 GiB per pod | Direct parity with ADR-017's/ADR-024's 1 vCPU/2 GiB starting point for a web/API tier that isn't itself compute- or memory-heavy |
| Min / max replicas | 3 / 10 | Direct parity with ADR-010/ADR-017/ADR-024's 3-10 range — see those ADRs for how the range was estimated from the same ~410,000 active-patient population and 8-12 second peak-load-time figures used throughout this case study; reused unchanged since the demand-side numbers are platform-independent |
| Load balancing (internal) | NSX Advanced Load Balancer (Avi), fronting the Tanzu Portal Deployments | The VCF-native L4/L7 load-balancing product, bundled with the platform ADR-026 already chose — the private-cloud analog to a hyperscaler's internal/regional load balancer |
| Public entry point | A third-party SaaS CDN/WAF product (e.g., a managed edge-security service such as Cloudflare or Akamai), configured to proxy traffic to the colocation facilities' public IP space, with the origin load balancer accepting connections only from the CDN/WAF vendor's published IP ranges | The named gap from the Rationale above — this is the mechanism that closes it. Origin-IP allowlisting keeps the colocation facilities' public entry point from being reachable by anyone bypassing the CDN/WAF layer |
| VPC/network integration | Application Tier-1 segment (ADR-029) | What lets the Portal reach the SQL Server VMs (ADR-028) over the private NSX fabric rather than a public connection string |

**Where the 3-10 range comes from.** Identical to every sibling ADR, reused unchanged since these are demand-side figures, not platform-specific ones — see ADR-024's Proposed Configuration for the full derivation. This estimate should be validated against real telemetry in the first 90 days after launch, the same "provisional starting point" discipline applied throughout this case study. Cost for this configuration, including the third-party CDN/WAF subscription, is deliberately not estimated here and stays with Step 13.

See [`../docs/application-architecture-private-cloud.md`](../docs/application-architecture-private-cloud.md) §2 for the full hosting narrative. No detail diagram exists yet for this ADR — hand-drawn diagrams are added incrementally and checked against this document once available.
