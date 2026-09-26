# ADR-012: Azure-Track Models and AI Gateway — Foundry Data Zone US behind API Management

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 5 pipeline

## Context

[ADR-004](ADR-004-ai-gateway-and-model-access.md) requires a single gateway, model admission only with no-training plus ZDR terms in the US (or in-tenancy models), immutable audit, metering, and budgets.

Azure AI Foundry documents the following:
- Prompts and completions are **not used to train** models.
- **Data Zone** deployments in a US resource process data **within the United States**.
- **Modified abuse monitoring (zero data retention)** is available to managed customers **by application**.
- **Claude models are available "Hosted on Azure" with Data Zone Standard (US).** Processing happens on Azure infrastructure, but **Anthropic is the independent data processor** under its own DPA.

API Management provides AI-gateway policies (`llm-token-limit`, LLM logging, semantic caching).

## Decision

- **A5 (models):** Foundry **Data Zone US** deployments of (a) Azure OpenAI models and (b) Claude hosted on Azure. Both are admitted only after two conditions are met:
  1. Microsoft's **modified-abuse-monitoring approval** is granted.
  2. Anthropic's DPA terms are reviewed by Harborline legal against NFR-4.

  Stateful APIs that store content (Assistants, stored completions) are **disabled** by policy. Only stateless inference is used.
- **A4 (gateway):** **Azure API Management** in internal mode is the only route to models. It handles:
  - Entra authentication and use-case identification
  - `llm-token-limit` budgets per use case, with fallback to a smaller admitted model at the limit
  - a policy check against G4 approvals
  - a redaction pre-processor for data classes not permitted for the use case
  - full LLM request and response logging to the audit store
- **A6 (audit):** logs go to **immutable Blob storage** (WORM, 7-year time-based retention, legal hold), with a Delta copy for analysis.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Mosaic AI Gateway as A4.** It is capable (usage tracking, inference tables, guardrails), but A4 must front *all* Harborline applications, including non-Databricks ones. API Management is the enterprise API front door Harborline would run anyway.
2. **Anthropic-hosted Claude through Foundry (Global Standard).** Rejected. Microsoft's documentation says data "might be processed outside of Azure including outside of your selected Azure region", which fails NFR-4's US-only requirement.
3. **Default abuse monitoring (without the ZDR approval).** Rejected as a go-live state, because it does not meet the zero-retention term in NFR-4.

## Consequences

- **Positive:** Two frontier model families are available under US-zone processing through one gateway. That is strong model choice and a strong fallback path against NFR-4.
- **Negative / accepted trade-off:** **Go-live depends on two external approvals** (Microsoft's ZDR application, and legal sign-off on Anthropic's processor terms). This is a named gate in Step 11.
- **Negative / accepted trade-off:** The gateway's redaction and G4-check logic are Harborline-built policy extensions, and they must be tested with the red-team suite.
