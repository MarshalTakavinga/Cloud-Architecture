# ADR-008: FinOps Allocation and Unit-Cost Model

**Status:** Approved
**Date:** Step 5 of the Case Study 5 pipeline

## Context

Driver 5 and NFR-11 set three requirements:
- 100% of spend tagged and allocated
- the steady-state data-platform run cost at or below the **$6.8M/yr** legacy baseline, excluding the AI capability
- the assistant at **≤ $0.05 per query** all-in, reported monthly

Consumption-priced warehouses and token-priced inference are both easy to overrun, and both are hard to attribute after the fact unless metering is designed in.

## Decision

**1. Mandatory tags on every resource and workload:**
- `cost-center`
- `use-case` (as registered in G4)
- `data-domain`
- `environment`
- `owner`

Untagged resources are denied at creation by policy. Untaggable shared costs (network, catalog) are allocated by a published formula.

**2. Metering points:**

| Where | What is metered | Allocated to |
|---|---|---|
| AI Gateway (A4) | Input and output tokens, model, and calls, per use case and user | Use case and business unit |
| Retrieval (A2/A3) | Queries and index storage per tier | Use case |
| Document Pipeline (I3) | Extraction, OCR, and embedding volume | The assistant use case (ingestion is an AI cost) |
| Lakehouse compute | **Separate compute pools per workload class** (ELT, BI, actuarial, data science, migration dual-run) | Data domain and team |
| Storage | By layer and domain | Data domain |

**3. Unit costs, reported monthly:**
- **Cost per assistant query** = gateway + retrieval + index share + pipeline share + audit storage, divided by queries
- **Cost per claim handled** = total platform cost ÷ claims closed
- **Cost per active report**
- **Data-platform run-rate** against the $6.8M baseline

**4. The $0.05 query budget.** An illustrative decomposition, to be verified with real prices per track:

| Component | Share |
|---|---|
| Generation (roughly 6K tokens of retrieved context in, 500 out, on a mid-tier frontier model) | ≈ $0.02–0.03 |
| Retrieval, rerank, index share | ≈ $0.005 |
| Audit and logging | ≈ $0.001 |
| Headroom | ≈ $0.015 |

**The main levers are context size (ADR-006 chunking and rerank quality) and model routing** (smaller models for simple lookups, frontier models for summaries).

**5. Controls:**
- **Hard budgets per use case at the gateway**, with alerts at 80% and throttling at 100%. Throttling degrades to a smaller admitted model before it refuses.
- **Auto-suspend and auto-scale** limits on lakehouse compute pools.
- **Anomaly alerts** on daily spend by tag.
- **Showback** in Year 1, then **chargeback** from Year 2, once baselines are trusted.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Monthly invoice analysis after the fact.** It cannot attribute shared warehouse compute or token spend to use cases, and it finds overruns a month late.
2. **One shared compute pool for all workloads.** It is simpler and marginally cheaper, but it makes allocation guesswork, and it lets a runaway data-science job slow down the reserving close.

## Consequences

- **Positive:** NFR-11 becomes measurable per use case from day one, and the AI capability must justify itself on its own unit economics, as driver 5 requires.
- **Positive:** Workload isolation protects the reserving close (NFR-8) from ad hoc analytics, and the dual-run cost of the Teradata migration becomes visible as its own line.
- **Negative / accepted trade-off:** The tagging discipline and the allocation formula need an owner. A FinOps function (at least one analyst) is part of the operating model, and it is costed in Step 12.
