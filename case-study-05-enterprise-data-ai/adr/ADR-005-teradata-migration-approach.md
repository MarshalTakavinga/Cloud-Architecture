# ADR-005: Teradata Migration Approach — Rationalize, Translate, Re-Layer, Dual-Run by Domain

**Status:** Approved (approach). Timing and the bridge-extension decision are deferred to Step 11.
**Date:** Step 4 of the Case Study 5 pipeline

## Context

Teradata holds about 450 TB raw, about 1,800 stored procedures and macros, BTEQ scripts, and the targets of about 2,400 Informatica jobs. It feeds about 14,000 reports, roughly 70% of which have not been opened in 12 months. Notice is due on 31 December 2026 and the term ends on 30 June 2027, with a one-year bridge at +25% available. `requirements.md` assumes 25–35% of the procedural logic needs manual rewrite.

## Decision

1. **Rationalize first.** Retire unused reports (about 70%) and orphaned Informatica jobs (about 30%) **before** migrating anything. Effort follows what is actually used.
2. **Translate, don't re-model, the bulk.** Automated SQL translation (Teradata SQL, BTEQ, and procedures into the target platform's SQL) handles most of the logic. The rest is rewritten as version-controlled ELT transformations. The existing integrated model is carried into silver and gold largely as-is.
3. **Re-model only the conformed core** (customer, policy, claim, loss), because driver 4 and NFR-8 need it and the three-estate problem cannot be fixed by translation.
4. **Migrate and dual-run by domain** (for example: claims, then policy and billing, then reserving and actuarial, then regulatory). Each domain runs in parallel with automated reconciliation (row counts, control totals, key report outputs) until it is signed off. Then its Teradata objects are frozen, and finally dropped.
5. **Stop new Teradata development now.** From the decision date, every new requirement lands on the new platform.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Lift everything unchanged, then optimize later.** It migrates the ~70% of reports nobody uses and the ~30% of jobs nobody consumes, and it spends the limited time before the Teradata dates on dead weight.
2. **Re-model the entire warehouse on the new platform.** It is the "right" long-term design but infeasible against the Teradata dates, and it would delay every domain until the whole model was done.
3. **A big-bang cutover of all domains at once.** Reconciliation risk would be concentrated at a single point in a regulated reporting environment, with no rollback short of staying on Teradata.

## Consequences

- **Positive:** Effort is proportional to value, and each domain's exit from Teradata is independently verifiable.
- **Positive:** The conformed core, which is the part driver 4 needs, gets real design attention instead of being translated as-is.
- **Negative / accepted trade-off:** Dual-running means paying for both platforms during migration. Its duration is the main lever on whether the bridge extension is needed, and it is decided in Step 11 with the cost modeled in Step 12.
- **Negative / accepted trade-off:** Translation tooling quality differs by target platform, and it directly affects the 25–35% manual-rewrite estimate. It is a scored item under "Teradata migration fit" in Step 9.
