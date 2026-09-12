### ADR-026: GCP customer identity provider

**Context:**
`logical-design.md` §1 named the Identity Provider as new  current-state has no dedicated identity component; customer sign-in and session handling are folded into the SCE monolith today. `requirements.md` §2 requires serving customers across the US, Canada, UK, Germany, France, Australia, and Singapore, growing 15–20% year-over-year on top of 2.4M existing accounts. This is a consumer identity population  millions of retail customers signing in with email/password or social login  not a workforce directory, which shapes which GCP identity product actually fits, the same framing ADR-010 and ADR-018 applied on the other two tracks.

**Options considered:**
- Google Cloud Identity, the workforce-oriented directory and federated-access product, extended to also hold customer identities.
- Google Cloud Identity Platform (built on Firebase Authentication)  GCP's purpose-built consumer-identity-and-access-management product.
- A third-party CIAM product (e.g., Auth0, Okta CIC) integrated via OpenID Connect.

**Decision:**
Google Cloud Identity Platform, configured as Solstice's dedicated customer-facing identity provider, issuing OAuth2/OIDC tokens consumed by the API layer (ADR-028) and the Cart/Checkout & Payment services.

**Rationale:**
Extending Cloud Identity  built around federated workforce access to Google Cloud and integrated enterprise applications  to also hold millions of consumer identities is rejected for the same structural reason ADR-010 and ADR-018 rejected the equivalent extension on the other two tracks: a consumer population has a completely different scale, security posture, and self-service-signup pattern than a workforce directory built around employee provisioning and deprovisioning, and mixing them puts customer-facing sign-up traffic inside the same trust boundary that governs internal system access. Identity Platform is Google's purpose-built answer to exactly this population: self-service sign-up/sign-in flows, social identity federation (Google, Apple, Facebook, and others via SAML/OIDC), MFA support, and standard OAuth2/OIDC token issuance the rest of this design already expects. A third-party CIAM product was considered  several are mature, well-regarded options  but rejected for the same reason ADR-010 and ADR-018 rejected one: Solstice's requirement here doesn't call for a capability Identity Platform lacks, and a second identity vendor alongside Google Cloud's own workforce identity tooling adds a vendor relationship and integration surface without closing a capability gap.

One platform nuance worth naming plainly, and in the opposite direction from Cognito's region-scoped pools (ADR-018): Identity Platform is a project-level, effectively **global** service  Solstice does not need three separate regional identity deployments the way Cognito's region-scoped resources require; one Identity Platform configuration serves customers in every active region. This cuts both ways and is stated honestly here rather than presented as a clean simplification: unlike Cognito's explicit per-region pools (each provably storing that region's data) or Entra External ID's single tenant with a stated EU-residency configuration, Identity Platform does not currently offer the same first-party, per-tenant guarantee of exactly where a given customer's identity record is stored and processed. Identity Platform's multi-tenancy feature can logically separate EU customers from US/APAC customers within one project, but achieving a provable EU-data-residency guarantee specifically for identity records needs verification against Google Cloud's current data-location commitments for Identity Platform, rather than being assumed solved by tenant separation alone.

**Trade-off:**
The data-residency verification item named above is carried forward honestly as an open item, not resolved in this ADR  it should be checked explicitly before Step 11's migration planning, and carried into Step 9's decision matrix as a real point of platform comparison rather than treated as an equivalent line item to Cognito's or Entra External ID's more explicit regional guarantees. Identity Platform's consumer-identity feature set, like Cognito's, is newer and has a smaller install base than the most established third-party CIAM platforms  accepted for the same reason ADR-010 and ADR-018 accepted the equivalent trade-off: the core requirement here (self-service sign-up/sign-in, OIDC-compliant token issuance, social login federation, MFA support) is well within Identity Platform's current capability, and staying on a single vendor's identity stack keeps operational and support surface area smaller for a 22-person org.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Service | Google Cloud Identity Platform |
| Deployment | Single project-level configuration, not region-scoped  unlike Cognito, one deployment serves all active regions |
| Tenancy | Identity Platform multi-tenancy used to logically separate EU customers from US/APAC customers, pending verification of Identity Platform's current per-tenant data-location commitments for GDPR purposes |
| Sign-in methods | Email/password, plus social identity federation (Google, Apple) at launch |
| Token protocol | OAuth2 / OpenID Connect, JWT tokens, validated at the API layer (ADR-028) |
| MFA | Optional, step-up on high-risk actions (e.g., saved-payment-method changes)  not enforced on every sign-in, the same conversion-rate reasoning ADR-010 and ADR-018 applied on the other tracks |
| Data residency | Logical separation via multi-tenancy today; explicit verification of Identity Platform's data-location guarantees is an open item for Step 9/Step 11 |
| Session issuance | Short-lived access token + refresh token, validated per-request at the API layer, not per-service |

**Status:** Approved

---

See [diagram](../diagrams/gcp-customer-identity.png).
