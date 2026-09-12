# ADR-024: Private-Cloud Compute Platform for the New Real-Time Services and the Nightly Reconciliation Job

**Status:** Approved
**Date:** Step 9 of the Case Study 2 pipeline

## Context

As in every other track, [Step 5](../docs/logical-design.md)'s three new services (Hold/Release Adapter, Fraud Orchestration Service, Ledger-of-Intent Service application tier) and the nightly Reconciliation Process need a compute home — now on the VMware Cloud Foundation platform selected in [ADR-023](ADR-023-private-cloud-platform-and-facility-strategy.md). Every hyperscaler track in this case study specifically avoided a Kubernetes-based compute platform (AKS, EKS, GKE) because of `requirements.md`'s cloud-skills-gap constraint, each choosing a fully managed serverless-container product instead (Container Apps, Fargate, Cloud Run). No such fully managed, cluster-free container product exists on private infrastructure.

## Decision

The three always-on services run as containerized workloads on **VMware Tanzu Kubernetes Grid**, VCF's own integrated Kubernetes offering, in a dedicated Tanzu cluster. The nightly **Reconciliation Process** runs as a **Kubernetes CronJob** in the same cluster — the direct analog to Azure Container Apps Jobs, AWS's scheduled Fargate task, and GCP's Cloud Run Job, but here requiring the same underlying Kubernetes control plane as the three always-on services, not a separate serverless job primitive.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Standalone virtual machines**, one per service, with no container runtime at all. Rejected — this would abandon the one-consistent-deployable-artifact benefit every other track gets from a single container image, trading it for three separately patched, separately managed VM operating-system images — more operational burden, not less.
2. **A standalone Kubernetes distribution deployed independently on top of vSphere**, separate from VCF's own integrated Tanzu offering. Rejected — running a second, disconnected Kubernetes control plane and lifecycle alongside the one VCF already provides would duplicate operational work with no corresponding benefit; Tanzu is managed as part of the same platform [ADR-023](ADR-023-private-cloud-platform-and-facility-strategy.md) already selected.

## Consequences

- **Positive:** One consistent, containerized deployment pattern reused across all four new-build compute components, consistent with every other track's own "one consistent compute model" finding.
- **Negative / accepted trade-off, named plainly:** This is the one point in the entire case study where the cloud-skills-gap concern that ruled out AKS, EKS, and GKE on every hyperscaler track has **no escape hatch**. A private-cloud platform offers no fully managed, cluster-free serverless-container product — running containers on owned infrastructure means operating a Kubernetes control plane, full stop. This is the single largest, most honest operational cost of the private-cloud option in this entire case study, and it must be weighted heavily in Step 10's decision matrix, not treated as roughly equivalent effort to the other three tracks.
- **Carried to Step 13:** Tanzu cluster sizing (node count, resource allocation per service) and the CronJob's schedule and resource limits are a cost-and-sizing exercise, deferred to Step 13.
