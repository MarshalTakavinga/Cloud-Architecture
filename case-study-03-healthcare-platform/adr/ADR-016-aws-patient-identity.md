### ADR-016: Identity provider for patient-facing authentication on AWS

**Context:**
ADR-002's Zero Trust decision assumed a single identity provider verifying every call, and ADR-009 already established — platform-neutral in principle — that patients must be a deliberately separate identity population from staff. Staff and providers are already represented in Meridian's on-prem Active Directory; on AWS, that directory is extended via AWS Directory Service (see `aws-implementation.md` §5). Patients have no corporate directory account, and putting them in one would be both wrong (they aren't employees) and a security problem (it would mix a consumer population into the directory that also gates clinical-system access) — the identical reasoning ADR-009 used for Azure.

**Options considered:**
- Extend the workforce-facing AWS Directory Service for Microsoft AD to also hold patient accounts
- Amazon Cognito User Pools — a separate, consumer-facing identity product built for external users
- A patient login system built and hosted by the Portal application itself

**Decision:** Amazon Cognito User Pools, as a distinct identity population from workforce AWS Directory Service for Microsoft AD.

**Rationale:**
Building and hosting patient login directly in the Portal application means owning password storage, MFA, account recovery, and breach response for ~2 million patient identities — undifferentiated heavy lifting unrelated to what CareLink PM or the Portal actually do, and a direct security liability if done imperfectly, the same reasoning ADR-009 applied. Extending the workforce directory is worse, not better: it mixes a consumer population with materially different risk and lifecycle characteristics into the same directory that governs access to clinical systems, and every future workforce policy change now has to account for patient accounts it shouldn't affect. Amazon Cognito User Pools is purpose-built for exactly this split: native OIDC/SAML support the Portal already needs for federation, a hosted UI for login/registration/password reset, built-in MFA, and — critically — a genuinely separate identity boundary from the AWS Directory Service instance used for workforce authentication.

**Trade-off:**
This means the Portal integrates against two identity providers instead of one — more configuration, two sets of policies to reason about, and two places an identity-related incident could originate — the identical trade-off ADR-009 accepted for Azure. A second, AWS-specific point worth naming: Amazon Cognito's risk-based/adaptive authentication and device-trust capabilities are less mature than Microsoft Entra ID's Conditional Access and Identity Protection, which is a real, if smaller, gap on the *workforce* side (see ADR-014/`aws-implementation.md` §5 for how that's handled) — but for the patient population specifically, Cognito's feature set (MFA, hosted UI, standard OIDC/SAML, adaptive authentication for suspicious sign-ins) is proportionate to what a patient-facing consumer login actually needs, and the gap matters far less here than it does for staff Conditional Access. Accepted because collapsing patient and workforce identity into one directory trades a manageable integration cost now for a much harder-to-reverse governance problem later — the same call ADR-009 made.

**Status:** Proposed

See [`../docs/application-architecture-aws.md`](../docs/application-architecture-aws.md) §2 for how the Portal integrates both identity providers, and [`../diagrams/patient-identity-architecture-aws.png`](../diagrams/patient-identity-architecture-aws.png) for the full two-identity-provider architecture, including the AWS IAM Identity Center SSO hop on the workforce side and confirmation that the Portal reaches RDS Custom directly over a private path, not through API Gateway.
