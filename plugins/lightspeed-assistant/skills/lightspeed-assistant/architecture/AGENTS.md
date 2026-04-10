# Architecture

LightspeedProposal is a CRD-based pluggable platform. No hardcoded
proposal types — all routing is via composable CRs.

## Key Concepts

- **4-CRD composition:** Provider → Agent → Workflow → Proposal
- **3-phase lifecycle:** analysis → execution → verification (any skippable)
- **Dynamic per-proposal RBAC** with multi-layer policy enforcement
- **Retry loop** with failure history; auto-escalation after max attempts
- **Adapters** create proposals from external sources (AlertManager, ACS, custom)

## Topics

|crd-composition.md — How the 4 CRDs wire together (both)
|phases.md — Lifecycle phases, transitions, skip behavior, user actions (both)
|rbac.md — Per-proposal RBAC creation, policy layers (developer)
