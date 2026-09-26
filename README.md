# Cloud Architecture

A portfolio of six cloud-architecture case studies, each run through the same process  business problem, requirements, architecture options, vendor-neutral logical design, platform-specific implementations (Azure/AWS/GCP/private), a weighted decision matrix, a recommended target architecture, a migration roadmap with ADRs, and a cost/risk analysis  to demonstrate architecture judgment across platforms rather than certification recall.

## Case Studies

| # | Case Study | Angle | Status |
| --- | --- | --- | --- |
| 1 | [Global e-commerce platform](case-study-01-ecommerce-platform/) | Seasonal traffic spikes, global customer base  autoscaling, CDN, cost optimization | **Done** — all 12 steps complete: problem → requirements → architecture options → vendor-neutral design → three platform implementations (Azure/AWS/GCP) → decision matrix → target platform (AWS) → migration roadmap → cost/risk analysis |
| 2 | [Banking modernization](case-study-02-banking-modernization/) | Core banking/payments workload  security, resiliency, regulatory reporting | **Done** — all 13 steps complete: problem → current-state → requirements/NFRs → architecture options and target style → vendor-neutral logical design → four platform implementations (Azure/AWS/GCP/private cloud, ADR-005–ADR-028) → decision matrix (ADR-029, Azure wins at 85.0%) → target architecture → 5-phase rollout roadmap with a feature-flag kill-switch (ADR-030–ADR-031) → cost/risk analysis. Unlike Case Study 1, this is a net-new capability rollout (not a production cutover), so the migration roadmap decouples the one genuine migration item (the 2021 AWS account) from the board-committed payments deadline. |
| 3 | [Healthcare platform](case-study-03-healthcare-platform/) | On-premises appointment system, ~2M patients — HIPAA/compliance, HA/DR | **Done** — all 13 steps complete: problem → requirements → vendor-neutral design → four platform implementations (Azure/AWS/GCP/private) → decision matrix → target platform (Azure) → migration roadmap → cost/risk analysis |
| 4 | [Manufacturing / IoT](case-study-04-manufacturing-iot/) | Device fleet ingesting telemetry at scale , event-driven architecture, data pipelines | **Done** — all 12 steps complete (27 ADRs): Kestrel Industrial Components, 12 plants, IT/OT convergence. Edge-first design (Unified Namespace, IEC 62443 zones, genealogy exactly-once, four-lane outbox) → three platform tracks including the edge (Azure/AWS/GCP) → decision matrix (GCP narrowly, 3.95 vs Azure 3.83, with conditions) → security-first two-track roadmap → cost/risk analysis, whose trigger test shows the platform choice must be confirmed on real quotes at gate G0 |
| 5 | [Enterprise data and AI platform](case-study-05-enterprise-data-ai/) | Data analytics and AI/RAG  data architecture, FinOps | **Done** — all 12 steps complete (30 ADRs): Harborline Mutual, a P&C insurer with a Teradata exit and a governed claims RAG assistant. Three cloud tracks, each weighing native vs. Databricks/Snowflake → GCP-native selected (ADR-027, 3.90 vs Azure 3.68), gated by G0 → three-track roadmap (assistant decoupled from the exit, Teradata bridge) → cost/risk analysis: data platform at 27% of the $6.8M baseline, assistant at $0.033/query, and gate A2 corrected so it no longer fails by construction |
| 6 | [Hybrid / private-cloud modernization](case-study-06-hybrid-private-cloud/) | Existing data-center estate extending into public cloud via VCF, Azure Arc, or Anthos | Not started |

## Structure

Each case study is a self-contained folder following the same layout:

```
case-study-NN-name/
│
├── README.md              # scenario summary + status for this case study
├── docs/
│   ├── current-state.md       # on-prem / as-is architecture
│   ├── problem-statement.md   # business problem, drivers, stakeholders
│   └── requirements.md        # NFRs, requirement/constraint/assumption/risk
│
├── adr/                    # architecture decision records
├── architecture/
│   ├── context/                # executive context view
│   ├── solution/                # solution / physical deployment
│   ├── network/                # network architecture
│   ├── security/                # security architecture
│   ├── data/                    # data architecture
│   └── dr/                      # HA/DR architecture
├── terraform/               # IaC, populated once a platform is chosen
└── diagrams/                # diagrams-as-code / exported diagrams
```

## Currently Active

[Case Study 6 — Hybrid / Private-Cloud Modernization](case-study-06-hybrid-private-cloud/) is next. Case Studies 1–5 are complete (Case Study 2's diagrams and Bicep IaC are deferred; the Case Study 4 and 5 diagrams exist as Mermaid reference sources awaiting hand-drawn versions).
