### ADR-010: Azure customer identity provider

**Context:**
`logical-design.md` §1 named the Identity Provider as new — current-state has no dedicated identity component; customer sign-in and session handling are folded into the SCE monolith today. `requirements.md` §2 requires serving customers across the US, Canada, UK, Germany, France, Australia, and Singapore, growing 15–20% year-over-year on top of 2.4M existing accounts. This is a consumer identity population — millions of retail customers signing in with email/password or social login — not a workforce directory, which shapes which Azure identity product actually fits.

**Options considered:**
- Microsoft Entra ID (the workforce tenant product) extended to also hold customer identities.
- Microsoft Entra External ID — Microsoft's customer-identity-and-access-management (CIAM) product, purpose-built for external/consumer sign-in scenarios, successor to Azure AD B2C.
- A third-party CIAM product (e.g., Auth0, Okta CIC) integrated via OpenID Connect.

**Decision:**
Microsoft Entra External ID, configured as Solstice's customer-facing identity tenant, issuing OAuth2/OIDC tokens consumed by the API Gateway (ADR-012) and Cart/Checkout & Payment services.

**Rationale:**
Extending a workforce Entra ID tenant to also hold millions of customer identities is rejected for the same structural reason Case Study 3 kept patient identity separate from its workforce tenant (ADR-009 there): a consumer population has a completely different scale, security posture, and self-service-signup pattern than a workforce directory built around employee provisioning/deprovisioning, and mixing them puts customer-facing sign-up traffic inside the same trust boundary that governs internal system access — a real, avoidable blast-radius increase. Entra External ID is Microsoft's purpose-built answer to exactly this population: self-service sign-up/sign-in flows, social identity provider federation, and a pricing/scale model built for consumer volumes, all while still issuing standard OAuth2/OIDC tokens the rest of this Azure design already expects. A third-party CIAM product was considered — several are mature, well-regarded options — but rejected specifically because Solstice's identity requirement here doesn't call for a capability Entra External ID lacks; introducing a second identity vendor alongside the workforce Entra ID tenant Solstice already needs for its own staff/admin tooling would add a vendor relationship and an integration surface without buying a capability gap Entra External ID doesn't already close.

**Trade-off:**
Entra External ID is a comparatively newer product in Microsoft's identity portfolio (the successor to Azure AD B2C), with a smaller install base and fewer years of production hardening than the more established third-party CIAM products. Accepted because the core requirement here — self-service consumer sign-up/sign-in, OIDC-compliant token issuance, social login federation, MFA support — is well within its current capability, and staying on a single vendor's identity stack (alongside the workforce Entra ID tenant) keeps operational and support surface area smaller for a 22-person engineering org that per ADR-002 isn't staffed for a sprawling toolchain.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Service | Microsoft Entra External ID |
| Tenant | Dedicated customer tenant, separate from Solstice's workforce Entra ID tenant |
| Sign-in methods | Email/password, plus social identity federation (Google, Apple) at launch |
| Token protocol | OAuth2 / OpenID Connect, JWT access tokens validated at the API Gateway (ADR-012) |
| MFA | Optional, step-up on high-risk actions (e.g., saved-payment-method changes) — not enforced on every sign-in the way Case Study 3 enforced workforce MFA, since a consumer storefront's UX cost of mandatory MFA on every login is a real conversion-rate risk this case study's own latency/conversion concerns (`problem-statement.md` §3) argue against |
| Data residency | EU customer identity data stored in Entra External ID's EU data region, consistent with `requirements.md` §3's GDPR residency requirement |
| Session issuance | Short-lived access token + refresh token, validated per-request at the API Gateway, not per-service |

**Status:** Approved

---

See [`../diagrams/azure-customer-identity.png`](../diagrams/azure-customer-identity.png) for the detailed diagram matching this ADR's Decision — the consumer sign-in flow through Entra External ID's dedicated customer tenant (self-service sign-up/sign-in, social identity federation, optional step-up MFA, EU data residency), token issuance and validation at the API Gateway (ADR-012), and the full Proposed Configuration table. Checked against this ADR's own text and `application-architecture.md`'s per-service identity summary before being finalized: an early draft showed Inventory & Order Orchestration (ADR-008) as a fourth service receiving "Authorized Access" behind API Management alongside Storefront & Catalog, Cart, and Checkout & Payment — but per `application-architecture.md`, Order Orchestration has no public entry point, no HTTP ingress, and no user-facing identity at all ("service-to-service via managed identity"), so it never consumes a customer token from this ADR's flow — removed. Storefront & Catalog's box was annotated "optional token use for personalization" to reflect that browsing itself requires no token (application-architecture.md §1).
