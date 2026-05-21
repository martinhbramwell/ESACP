# ESACP — Orientation for new operators and onboarding authors

Read this first. It is deliberately short.

## What ESACP is

ESACP is an **AI-assisted platform for unifying a small business's
scattered data into a single ERPNext-based source of truth**.

Its target audience is small businesses operating across a patchwork
of SaaS and desktop tools — accounting in one place, online sales in
another, in-person sales in a third, customer data in a fourth, tax
filing in a fifth — that want to consolidate around one ERP, but
cannot justify the cost of a dedicated ERP consultant. ERPNext is the
system ESACP wraps; the platform's job is to make ERPNext approachable,
maintainable, and extensible for that audience, with an AI assistant
as the day-to-day expert.

The platform combines:

- A **controller machine** (the operator's workstation) that bootstraps
  everything else.
- A **hypervisor** that hosts a fleet of VMs (an observability hub plus
  one or more ERPNext target VMs).
- A **pipeline** of small Python primitives that does every
  infrastructure operation (VM build, WireGuard mesh, ERPNext
  installation, observability stack, MCP server setup).
- A **Cytoscape-based control plane** for the operator to inspect and
  drive the fleet.
- **MCP connectors** (MariaDB, ERPNext, Grafana, etc.) that give an AI
  assistant first-class read/write access to the running ERP system.

The MCP layer is the point. The rest is infrastructure that makes
the MCP layer reliable.

## Who ESACP is for

ESACP is **not a turnkey product**. It targets small businesses that
share a common posture:

- **Data scattered** across multiple "sources of truth". The typical
  small-business shape uses one specialised tool per category:
  - *Accounting / bookkeeping* — QuickBooks Online, Xero, Sage
    Accounting, FreshBooks, Wave, Zoho Books
  - *Online sales channels* — Shopify, WooCommerce, Etsy, Amazon
    Seller Central, eBay, BigCommerce
  - *In-person sales / POS / payments* — Square, Clover, Stripe,
    Lightspeed, PayPal Here
  - *CRM / contacts / marketing* — HubSpot, Zoho CRM, Pipedrive,
    Salesforce Essentials, Mailchimp
  - *Payroll / HR* — Gusto, ADP Run, BambooHR, Paychex, Zoho People
  - *Tax preparation* — TurboTax Self-Employed, TaxAct Business,
    H&R Block, country-specific tax-authority filing tools

  …with spreadsheets (Excel, Google Sheets, Apple Numbers) as the
  de facto glue between any two of the above.
- A **need to consolidate** around a single ERP system (ERPNext, in
  this project's case).
- A **budget that does not stretch** to a dedicated ERP consultant.
- A **willingness to operate the system with an AI assistant** as the
  day-to-day expert, rather than hiring one.

### Caveat — what the list above does and does not promise

The categorised list above describes the *target landscape* — the kinds
of tools real small businesses operate across. **It does NOT mean ESACP
ships turnkey connectors for any specific named product.** Whether a
given product can be integrated into an ESACP-driven ERPNext deployment
depends on three independent preconditions, each verified per product
at the moment the integration is attempted:

1. **API surface** — the product must expose a programmatic
   data-extraction interface (REST, GraphQL, RPC, webhooks, or an
   official MCP server) at the granularity ESACP needs.
2. **Terms of Service / EULA** — programmatic access must be explicitly
   permitted. Many SaaS terms allow API access only via the vendor's
   official developer programme, with app registration, rate limits,
   and data-use restrictions.
3. **ESACP + Claude Code capability** — once API and EULA permit
   access, ESACP must have a working connector (or be able to build one
   on demand), and Claude Code must be able to operate it as either a
   one-time migration or an ongoing exchange. Today, neither is
   universal — each integration is its own piece of work.

Indicative readiness by category, subject to per-product validation
before any integration work begins:

| Category | Generally good API + permissive terms | Mixed / partner-gated | Limited or export-only |
|---|---|---|---|
| Accounting | QuickBooks Online, Xero, Zoho Books, FreshBooks | Sage (varies by product), Wave (post-acquisition uncertainty) | — |
| Online sales | Shopify, WooCommerce, BigCommerce | Amazon Seller Central (SP-API onboarding non-trivial), Etsy (seller-data restrictions) | — |
| POS / payments | Square, Stripe, Clover, Lightspeed | PayPal Here (data via PayPal merchant APIs) | — |
| CRM / contacts | HubSpot, Zoho CRM, Pipedrive, Mailchimp | Salesforce Essentials (rich APIs, complex auth) | — |
| Payroll / HR | Gusto, BambooHR, Zoho People | ADP Run, Paychex (partner-programme gated) | — |
| Tax | — | — | TurboTax, TaxAct, H&R Block (user-driven PDF/CSV export only); country-specific filing tools vary widely |

This table is general knowledge as of authoring, not a validated
integration matrix. Treat every cell as a starting point that needs
re-verification (vendor docs + current EULA + ESACP connector status)
at the moment of integration.

Two recognisable variants of this audience:

1. **Greenfield consolidation** — a small business not yet on any ERP,
   with data fragmented across the SaaS/desktop tools above, looking
   to migrate onto ERPNext as their first ERP.
2. **Maintainer-dependent customisation** — a small business that has
   already built a customised ERPNext deployment and cannot afford to
   lose the developer who built it.

Both variants want the same thing: an ERP they can keep running and
evolving with AI assistance, without continuous expert contracting.

## What this branch is for

This is the `on_boarding` branch. Its job is to produce the
**new-operator onboarding material** — the protocols, documentation,
and code that take a new operator from first encounter with ESACP all
the way to a fully staged deployment.

You (the fresh Claude reading this) are the **author** of that
onboarding material. The end-user (a new operator who has never seen
ESACP before) is the **consumer**.

Both populations have zero prior knowledge of any specific tenant. The
branch must therefore be self-contained: nothing on this branch may
assume tenant-specific names, hostnames, secrets, or business logic.

## The end-user journey the onboarding material must cover

The new operator's path runs in four stages:

1. **First encounter with ESACP** — what it is, what it solves, what
   posture it asks the operator to adopt, what hardware/accounts are
   needed.
2. **Preparing a controller machine** — OS choice, prerequisites, repo
   clone, SSH keys, secrets (SOPS/age), GPG signing, basic toolchain.
3. **Using the controller to prepare the first local KVM VMs** —
   hypervisor setup on a target host, WireGuard mesh, observability
   hub VM, a first ERPNext target VM, validating the fleet through
   the Cytoscape UI.
4. **Reaching a staged VPS master + slave** — moving from local KVM to
   a cloud-VPS deployment, the master/slave pairing, replication and
   failover posture.

The deliverable is the **material** that walks an operator through
those four stages, not the stages themselves running. The fresh Claude
on this branch authors that material; an end-user later follows it.

## Scope

### In scope (S69+ work on this branch)

- Operator-facing documentation for each of the four stages above,
  pitched at zero-knowledge readers.
- Screenshots, walkthroughs, and (where useful) recorded sessions.
- Code or scripts that streamline the operator's path through the
  four stages — but only where the existing pipeline does not already
  cover the case and where the addition serves first-time-operator
  ergonomics, not power-user productivity.
- A self-check the operator can run after each stage to confirm they
  are where they think they are.

### Out of scope (do not pull these into the branch)

- Tenant-specific business logic, bespoke apps, customised DocTypes,
  or migration history.
- Multi-tenant operations.
- Production cutover procedures, V13→V14→V15→V16 migration playbooks.
- Cloud-orchestration backends beyond a single VPS master + slave
  (no CloudStack, no Kubernetes).
- Observability stack design beyond first-contact-with-Grafana for
  the new operator.
- Anything that requires the operator to already have an opinion
  about ERPNext internals. Onboarding assumes none.

## What this branch is NOT for

This branch is not a place to develop new platform features, refactor
the pipeline, change MCP-connector behaviour, touch the Cytoscape
control plane's data model, or modify any code outside the
`on_boarding/` tree. If a defect in the platform shows up while
authoring onboarding material, file an issue on the upstream tracker
and continue with the onboarding work — do not fix the platform from
this branch.

## Next steps

Read [`POINTERS.md`](POINTERS.md) for the map into ESACP's existing
repo-resident technical surface (what files exist, what each is for,
which are universal vs. tenant-specific).

Then read [`AI_GUARDRAILS.md`](AI_GUARDRAILS.md) for the conduct and
process rules you are expected to follow while working on this branch.

Then read [`README.md`](README.md) for the kit index and the
first-session checklist.
