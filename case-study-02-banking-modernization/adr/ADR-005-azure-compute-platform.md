# ADR-005: Azure Compute Platform for the New Real-Time Services

**Status:** Approved
**Date:** Step 6 of the Case Study 2 pipeline

## Context

[Step 5](../docs/logical-design.md) defined three new, greenfield services that need a compute platform on Azure: the Hold/Release Adapter, the Fraud Orchestration Service, and the Ledger-of-Intent Service (application tier). All three are stateless request/event handlers, share the same deployment cadence, and carry the same latency-sensitive constraint — NFR-4 requires fraud-scoring decisions in ≤300ms, and NFR-3 requires end-to-end posting latency ≤5 seconds. Requirements.md also flags a cloud-skills gap at Palisade: this is a bank whose engineering organization has run a mainframe and a vendor-licensed digital banking platform, not a Kubernetes estate.

## Decision

All three services run on **Azure Container Apps**, each as its own container app within the same Container Apps Environment, with a minimum replica count of 2 per service to avoid cold-start latency on the fraud-scoring and hold/release paths. Azure Container Apps' built-in KEDA-based autoscaling handles the payment-volume variability described in `requirements.md`, and its managed control plane (no cluster to patch or upgrade) directly addresses the cloud-skills-gap constraint.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Azure Kubernetes Service (AKS).** Rejected — AKS gives more low-level control than this workload needs (three uniform, stateless services, not a large heterogeneous microservices estate), and its operational overhead — cluster upgrades, node-pool management, add-on patching — falls directly on a team `requirements.md` already flags as short on cloud-native skills. Case Study 1 chose AKS-equivalent orchestration because it had a more complex, multi-team service topology; that reasoning does not transfer here.
2. **Azure App Service.** Rejected — App Service is a strong fit for a web application, but these three services are event- and request-driven backend processors, not web front ends, and App Service's scaling model is less naturally suited to the event-bus-triggered invocation pattern the Fraud Orchestration Service and Ledger-of-Intent Service use.
3. **Azure Functions (event-driven, serverless).** Rejected as the *primary* platform for the fraud-scoring path specifically — Functions' consumption-plan cold starts are difficult to bound tightly enough against NFR-4's 300ms budget, and a bank-grade fraud check going cold-start-slow on exactly the transactions the FedNow deadline is built around is an unacceptable risk. Functions remains a candidate for genuinely bursty, non-latency-critical peripheral work (e.g., notification fan-out), but that is a Step 13 sizing detail, not a Step 6 architectural decision.

## Consequences

- **Positive:** One consistent compute model across all three new services simplifies operations, observability, and the team's learning curve — directly responsive to the cloud-skills-gap constraint.
- **Positive:** KEDA-based autoscaling on Container Apps means capacity follows real-time-payment volume without a human resizing anything, consistent with driver 4 (rising cost pressure) — idle capacity is not paid for at 3am when FedNow volume is low.
- **Negative / accepted trade-off:** Container Apps offers less low-level infrastructure control than AKS would (e.g., custom CNI, node-level tuning). This is accepted because none of the three services need that control today; if a future capability genuinely requires it, that is a new decision to revisit, not a gap in this one.
- **Carried to Step 13:** Exact replica counts, CPU/memory allocation, and scaling thresholds are a cost-and-sizing exercise, deferred to Step 13 by this case study's convention.
