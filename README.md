# Cloud Architecture

A portfolio of six complete cloud-architecture case studies, each run through the same 13-step pipeline (business problem → requirements → architecture options → vendor-neutral logical design → Azure/AWS/GCP/private implementations → decision matrix → recommended target architecture → migration roadmap & ADRs → cost/risk analysis), built to demonstrate architecture judgment across platforms rather than certification recall.

Companion reference material (principles, frameworks, ADR templates, diagramming conventions) lives in a separate personal reference guide and is not duplicated here — each case study links back to the relevant section by number.

## Case Studies

| # | Case Study | Angle | Status |
| --- | --- | --- | --- |
| 1 | [Global e-commerce platform](case-study-01-ecommerce-platform/) | Seasonal traffic spikes, global customer base — autoscaling, CDN, cost optimization | Not started |
| 2 | [Banking modernization](case-study-02-banking-modernization/) | Core banking/payments workload — security, resiliency, regulatory reporting | Not started |
| 3 | [Healthcare platform](case-study-03-healthcare-platform/) | On-premises appointment system, ~2M patients — HIPAA/compliance, HA/DR | **In progress** — current-state architecture, problem statement, and preliminary requirements done |
| 4 | [Manufacturing / IoT](case-study-04-manufacturing-iot/) | Device fleet ingesting telemetry at scale — event-driven architecture, data pipelines | Not started |
| 5 | [Enterprise data and AI platform](case-study-05-enterprise-data-ai/) | Data analytics and AI/RAG — data architecture, FinOps | Not started |
| 6 | [Hybrid / private-cloud modernization](case-study-06-hybrid-private-cloud/) | Existing data-center estate extending into public cloud via VCF, Azure Arc, or Anthos | Not started |

## Structure

Each case study is a self-contained folder following the same layout:

```
case-study-NN-name/
│
├── README.md              # scenario summary + pipeline status for this case study
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

[Case Study 3 — Healthcare Platform](case-study-03-healthcare-platform/) is the one being actively built. See its README for pipeline status and what's next.
