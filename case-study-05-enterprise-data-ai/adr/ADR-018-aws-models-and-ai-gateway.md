# ADR-018: AWS-Track Models and AI Gateway — Bedrock US Profiles behind a Harborline Gateway

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 5 pipeline

## Context

[ADR-004](ADR-004-ai-gateway-and-model-access.md) requires one gateway and only no-training, zero-retention models with US processing. On Bedrock:
- Model providers **"don't have access to Amazon Bedrock logs or to customer prompts and completions"**.
- **Geographic (US) cross-region inference profiles** keep processing in the US.
- **Models that require provider-mandated human review** (currently the **Claude Fable 5 / 5.1** tier) require `aws_review` data retention: prompts and completions are **"retained within the AWS boundary for up to 30 days"** for review.

AWS offers **Bedrock Guardrails** (including sensitive-information filters), **model-invocation logging**, and **application inference profiles** (taggable per use case). It has no first-party enterprise LLM gateway equivalent to Azure API Management's AI policies.

## Decision

- **A5 (models):** **Bedrock** through **US geographic inference profiles** only. An SCP denies global profiles and non-US regions.
  - **Admitted:** models with no review-retention requirement, including the non-review Claude models and a smaller model for simple lookups and fallback.
  - **Not admitted (by default):** models requiring `aws_review` retention, because they fail NFR-4's zero-retention term. The exception path is a documented legal and compliance decision recorded in G4.
- **A4 (gateway):** a **thin Harborline gateway service** on Fargate, built on an open-source LLM-gateway core, behind a private API Gateway endpoint. It provides:
  - use-case identification and the G4 check
  - budgets and fallback
  - **Bedrock Guardrails** for sensitive-data redaction
  - **one application inference profile per use case**, so cost allocation tags attach to every token
- **A6 (audit):** Bedrock invocation logging + gateway logs go to **S3 Object Lock (compliance mode, 7-year retention) with native legal hold**.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Applications calling Bedrock directly, with IAM plus Guardrails.** Rejected. There would be no central G4 check, and budgets and fallback would be re-implemented per application.
2. **Admitting review-tier models by default.** Rejected, because 30-day retention for human review contradicts NFR-4 as written.
3. **Mosaic AI Gateway or a commercial gateway product.** Not selected with an AWS-native data platform ([ADR-015](ADR-015-aws-data-platform.md)). A commercial gateway stays an option if the in-house service proves costly to maintain.

## Consequences

- **Positive:** Bedrock's provider isolation and US geo profiles meet NFR-4 cleanly for admitted models, with no separate ZDR application (unlike Azure, [ADR-012](ADR-012-azure-models-and-ai-gateway.md)). Object Lock gives native legal hold.
- **Negative / accepted trade-off:** **Harborline builds and runs the gateway.** It is on the critical path of every AI call, so it is more build than Azure's API Management policies.
- **Negative / accepted trade-off:** **The very top model tier is off-limits by default.** If Harborline's evaluation shows that tier is needed for quality, the retention exception becomes a governance decision, not an engineering one.
