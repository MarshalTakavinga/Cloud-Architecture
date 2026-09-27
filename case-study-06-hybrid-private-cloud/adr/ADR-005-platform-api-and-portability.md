# ADR-005: Platform API, Product Catalog, and Portability Rules

**Status:** Approved
**Date:** Step 4 of the Case Study 6 pipeline

## Context

- A VM takes an average of **12 business days**, through tickets.
- The digital team built three Rancher clusters outside infrastructure operations, and opened an AWS account (`current-state.md`).
- NFR-9 requires a standard VM in ≤ 4 hours and a namespace in ≤ 1 hour, both through an API.
- NFR-11, and the 2023 interagency third-party guidance, require a documented and **tested** exit path from the chosen platform.

## Decision

1. **A platform API with a product catalog:**
   - Standard products: VM sizes on approved images, network segments per zone, Kubernetes namespaces with quotas, and DNS and certificates.
   - Delivered through **Terraform** (or an equivalent) against the platform API.
   - **ServiceNow** is the approval and record system. Standard products in Tier 2 and dev/test are **approved automatically by policy**. Tier-0 and Tier-1 changes follow change approval.
2. **Pipeline-built golden images** for Windows and RHEL, patched monthly, with a CIS baseline and signed provenance.
3. **A platform-team-run, CNCF-conformant Kubernetes** replaces the three Rancher clusters. It has the same patching, monitoring, and policy as every other platform component.
4. **Portability rules:**
   - Images are built from source by the pipeline, so they can be rebuilt for another hypervisor.
   - Terraform modules isolate the provider-specific layer behind bank-owned module interfaces.
   - Application manifests use only conformant Kubernetes APIs, with no proprietary resource types in the application layer.
   - Backups are restorable to more than one hypervisor.
   - **An exit test runs annually:** a representative workload set, including one Tier-1 service, is moved off the platform, and the effort is recorded against the exit plan.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Faster tickets.** Rejected. It shortens the wait but keeps the incentive to route around it.
2. **A self-service portal without infrastructure as code.** Rejected as sufficient. Changes would not be reviewable, repeatable, or portable.
3. **Let delivery teams run their own Kubernetes.** Rejected. That is the current state, and it is how the clusters ended up outside patching.

## Consequences

- **Positive:** Delivery teams get minutes instead of weeks, so the incentive for shadow infrastructure goes away.
- **Positive:** The exit path is exercised every year, so it is real, and it gives the bank negotiating leverage at every renewal.
- **Negative / accepted trade-off:** Portability rules forgo some proprietary platform features in the application layer. They are allowed in the *platform* layer, where the exit plan accounts for them.
- **Negative / accepted trade-off:** Terraform and pipeline skills are new for most of the team (driver 5). The three automation engineers seed a platform team, and NFR-12's allowance for up to four hires is expected to be used here.
