# ADR-004: AI Gateway and Model Access Policy

**Status:** Approved
**Date:** Step 4 of the Case Study 5 pipeline

## Context

NFR-4 requires that customer data never trains third-party models, that retention be zero or the model be hosted in the tenancy, and that processing stay in the US. NFR-5 requires human-in-the-loop, NFR-6 an immutable AI audit trail for 7 years, and NFR-11 an assistant unit cost of $0.05 or less per query, reported monthly. The NAIC bulletin expects oversight of third-party AI. The March 2026 incident showed what happens when model access is unmanaged.

## Decision

**Every model call from every Harborline application goes through a single AI gateway.** It is responsible for:

- **Identity and authorization:** the calling application, use case, and end user.
- **Data-use policy:** which data classifications may reach which admitted models. Redaction is applied where policy requires it (for example, removing Restricted fields for a use case not entitled to them).
- **An immutable audit record** for every call: user, use case, prompt, retrieved source IDs, model and version, parameters, response, and the user's subsequent action. Records are retained 7 years and are subject to legal hold (NFR-6).
- **Metering and attribution:** tokens and cost per use case and business unit, with rate limits and budgets (NFR-11).
- **Routing and fallback** between admitted models.
- **Evaluation hooks:** the evaluation harness and red-team suite ([ADR-003](ADR-003-permission-aware-retrieval.md)) must pass before a new model, model version, or prompt version is admitted.

**Admission criteria for models:**
- a provider-hosted model under **contractual no-training and zero-data-retention** terms, with processing in a **US region**, *or*
- an **open-weight model hosted in Harborline's tenancy**

**Portability:** prompts, retrieval logic, and evaluation sets are kept **model-agnostic**. A model change is an evaluation run and an inventory update, not an application rewrite.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Applications calling model APIs directly.** Policy, audit, and cost attribution would then be re-built, or forgotten, per application.
2. **Consumer or public AI tools under an acceptable-use policy.** That is the March 2026 incident with a memo attached.
3. **In-tenancy open-weight models only.** Rejected as the *only* option, because it would forgo the quality and operational simplicity of provider-hosted frontier models that meet the same NFR-4 terms. It is kept as an admitted path, and as the fallback if provider terms change.

## Consequences

- **Positive:** Data-use policy, audit, and cost are enforced once, and the gateway's log *is* the evidence the NAIC bulletin and examiners ask for.
- **Positive:** The unit-cost NFR becomes measurable by construction, per query and per use case.
- **Negative / accepted trade-off:** The gateway is on the critical path of every AI interaction, so it needs the assistant's availability target (99.9% in business hours) and must add little latency against NFR-1.
- **Negative / accepted trade-off:** Which frontier models are available **in which US regions, under which data terms, on which platform** differs by cloud and changes often. It must be verified per track in Steps 6–8, and it is expected to be a major differentiator.
