# ADR-024: GCP-Track Models and AI Gateway — Vertex AI (US) behind Apigee

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 5 pipeline

## Context

[ADR-004](ADR-004-ai-gateway-and-model-access.md) sets the requirements. Google's Vertex AI data governance states that "Google won't use your data to train or fine-tune any AI/ML models without your prior permission or instruction". It also documents three things:
- Gemini models **cache data in memory for 24 hours by default**, and this can be **disabled per project**.
- Prompts may be logged for **abuse monitoring**, with an **exception** available on request.
- The statement covers "all managed models on Vertex AI". It does not cover partner models.

**Claude's US multi-region endpoint** (`locations/us`) reached GA on 15 May 2026, and keeps processing within the United States. **Apigee** provides LLM token policies, **Model Armor** integration, and semantic caching.

## Decision

- **A5 (models):**
  - **Gemini** (managed), with **in-memory caching disabled** for the AI projects and the **abuse-monitoring exception** granted before go-live.
  - **Claude via the US multi-region endpoint**, admitted after legal confirms the **partner-model data terms** against NFR-4.
  - Regional or US endpoints only. Global endpoints are denied by Organization Policy and IAM.
- **A4 (gateway):** **Apigee**, providing:
  - LLM token policies (quotas and budgets per use case, with fallback to a smaller model)
  - **Model Armor** for prompt and response screening and sensitive-data filtering
  - the G4 check
  - request and response logging
  - semantic caching **only** for non-Restricted reference-corpus answers, since caching claim-specific answers across users could leak
- **A6 (audit):** **Cloud Storage with Bucket Lock** (locked 7-year retention, object holds for legal hold) plus a BigQuery copy.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Global endpoints.** Rejected, because they fail NFR-4's US-only requirement.
2. **Leaving Gemini caching enabled.** Rejected, because 24 hours of in-memory retention contradicts a strict reading of zero retention.
3. **A Harborline-built gateway.** Unnecessary here, since Apigee provides the capability, like API Management on Azure.

## Consequences

- **Positive:** Two frontier model families (Gemini and Claude) are available in the US geography, behind a **bought** gateway with built-in prompt screening.
- **Negative / accepted trade-off:** **Contract gates:** the abuse-monitoring exception and the partner-terms review for Claude. These are the same class of gate as on Azure.
- **Negative / accepted trade-off:** Semantic caching has to be carefully scoped, because a cache is a cross-user data path.
