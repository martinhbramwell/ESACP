# Agenda — Next Session (2026-03-28 afternoon or later)

---

## Unfinished Business

### 1. Confirm Cloudflare MCP is working
First tool call should succeed without OAuth prompt.
If it fails: check `~/.mcp-auth/mcp-remote-0.1.38/` still exists; check token not corrupt.

### 2. Open GitHub Issues Review
`gh issue list --repo martinhbramwell/ESACP --state open`
Issues open: #9, #21, #23, #24, #26, #36, #37, #48

### 3. User's Deferred DNS/Cert Architecture Questions
User indicated more questions mid-session on 2026-03-28 ~08:00 — invite these first.

### 4. Subdomain Naming Scheme for iridium.blue — DECISION REQUIRED
Must decide before any DNS record creation, acme.sh role, or target3 re-provisioning.
Options: `lab.target3.iridium.blue` | `target3.dev.iridium.blue` | `lab.iridium.blue`
Reference: [DNS & Cert Architecture Planning](notes/2026-03-28-0800-dns-cert-architecture.md)

---

## New Business

### 5. [To be added]
