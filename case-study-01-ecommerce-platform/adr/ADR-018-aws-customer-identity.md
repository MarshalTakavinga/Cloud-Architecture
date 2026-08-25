### ADR-018: AWS customer identity provider

**Context:**
`logical-design.md` §1 named the Identity Provider as new — current-state has no dedicated identity component; customer sign-in and session handling are folded into the SCE monolith today. `requirements.md` §2 requires serving customers across the US, Canada, UK, Germany, France, Australia, and Singapore, growing 15–20% year-over-year on top of 2.4M existing accounts. This is a consumer identity population — millions of retail customers signing in with email/password or social login — not a workforce directory, which shapes which AWS identity product actually fits.

**Options considered:**
- AWS IAM Identity Center (the workforce-oriented federated access product) extended to also hold customer identities.
- Amazon Cognito User Pools — AWS's purpose-built consumer-identity-and-access-management product.
- A third-party CIAM product (e.g., Auth0, Okta CIC) integrated via OpenID Connect.

**Decision:**
Amazon Cognito User Pools, configured as Solstice's dedicated customer-facing identity pools, issuing OAuth2/OIDC tokens consumed by API Gateway (ADR-020) and the Cart/Checkout & Payment services.

**Rationale:**
Extending AWS IAM Identity Center — built around federated workforce access to AWS accounts and integrated applications — to also hold millions of consumer identities is rejected for the same structural reason ADR-010 rejected extending the workforce Entra ID tenant on Azure: a consumer population has a completely different scale, security posture, and self-service-signup pattern than a workforce directory built around employee provisioning and deprovisioning, and mixing them puts customer-facing sign-up traffic inside the same trust boundary that governs internal system access. Cognito User Pools is AWS's purpose-built answer to exactly this population: self-service sign-up/sign-in flows, social identity federation (Google, Apple, and others via SAML/OIDC), and native integration with API Gateway as a built-in authorizer type, all while issuing standard OAuth2/OIDC tokens the rest of this design already expects. A third-party CIAM product was considered — several are mature, well-regarded options — but rejected for the same reason ADR-010 rejected one on Azure: Solstice's requirement here doesn't call for a capability Cognito lacks, and a second identity vendor alongside AWS's own workforce identity tooling adds a vendor relationship and integration surface without closing a capability gap.

**Trade-off:**
Cognito's consumer-identity feature set is newer and has a smaller install base than the most established third-party CIAM platforms — accepted for the same reason ADR-010 accepted the equivalent trade-off on Azure: the core requirement here (self-service sign-up/sign-in, OIDC-compliant token issuance, social login federation, MFA support) is well within Cognito's current capability, and staying on a single vendor's identity stack keeps operational and support surface area smaller for a 22-person org.

One trade-off genuinely specific to this platform, worth surfacing plainly rather than smoothing over: Amazon Cognito User Pools are a **regional** resource, not a global one. There is no single "dedicated customer tenant" the way Azure's Entra External ID offers, configured once with a stated EU data-residency region. To keep EU customer identity data resident in the EU for GDPR purposes, this design requires a distinct Cognito User Pool per active region rather than one global pool — a real topology difference from the Azure track, not a naming difference, and it should be carried into Step 9's decision matrix as an actual point of comparison rather than treated as an equivalent line item.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Service | Amazon Cognito User Pools |
| Pools | One regional User Pool per active region (US, EU, APAC) — not a single global pool, since Cognito User Pools are region-scoped resources |
| Sign-in methods | Email/password, plus social identity federation (Google, Apple) at launch |
| Token protocol | OAuth2 / OpenID Connect, JWT access tokens, validated at API Gateway via a Cognito authorizer (ADR-020) |
| MFA | Optional, step-up on high-risk actions (e.g., saved-payment-method changes) — not enforced on every sign-in, the same conversion-rate reasoning ADR-010 applied on Azure |
| Data residency | Each region's customer identity data is created, stored, and processed within that region's own Cognito User Pool, consistent with `requirements.md` §3's GDPR residency requirement |
| Session issuance | Short-lived access token + refresh token, validated per-request at API Gateway, not per-service |

**Status:** Approved
