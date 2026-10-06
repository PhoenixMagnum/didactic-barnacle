# Repository Intelligence Cache

A living, stack-aware cache of open-source repositories that may be useful across House of Monakshi, StoryVault/writing, research, automation, AI/agents, publishing and future technical work.

This is deliberately **not** a giant install list. Every repository is classified as:

- **P0 — Core now:** already selected, already aligned, or immediately useful.
- **P1 — Strong next:** likely to solve a foreseeable problem without creating architectural chaos.
- **P2 — Reference/future:** keep nearby; adopt only when a concrete requirement appears.
- **P3 — Watch/experimental:** interesting, but too new, too heavy or too autonomy-oriented for current production use.

The cache contains **89 repositories** across 7 compatibility stacks.

## Non-negotiable operating rule

A repository enters the cache cheaply. It enters a real project expensively.

Before adoption, require:
1. a concrete problem,
2. stack compatibility,
3. active maintenance,
4. acceptable license/security posture,
5. a rollback path,
6. no duplication of a capability ChatGPT or the existing stack already provides.

## Current stack priority

1. **S1 Monakshi independent storefront** — protect and finish the existing Next.js/Tailwind/shadcn/GrapesJS/Supabase/Razorpay/React Email direction.
2. **S2 Monakshi operations + automation** — use connectors first; add n8n/Playwright/change detection only where durable automation pays for itself.
3. **S3 StoryVault writing + publishing** — keep deterministic, local-first and dependency-light.
4. **S4 Research + knowledge processing** — add extraction/RAG only around evidence, citations and source provenance.
5. **S5 ChatGPT / agent engineering lab** — experiment here, not inside canon or production by default.
6. **S0/S6 discovery + future infrastructure** — feed decisions without creating tool sprawl.

See [STACKS.md](./STACKS.md) for the compatibility map and [repos.json](./repos.json) for the machine-readable catalog.

## Self-refresh

The workflow at `.github/workflows/repository-cache-refresh.yml` runs weekly and regenerates `STATUS.md` using GitHub's repository API. It tracks current repository health metadata such as archive state, stars, default branch, license and last push.

The refresh script **never auto-promotes or auto-installs** a repository. Human architectural judgment remains the gate.

## Project isolation

- Monakshi production decisions stay inside the Monakshi stack.
- StoryVault canon remains authoritative and is not delegated to autonomous memory/RAG systems.
- Discovery repos, awesome lists and agent frameworks are reference material until explicitly promoted.
- Private supplier/customer/credential data never belongs in this public cache.


## Just-in-time repository scouting

The cache can now expand itself **without automatically installing anything**.

- `needs.json` defines recurring capability searches for the seven stacks.
- `scripts/scout.py` queries GitHub, removes repositories already in the cache, and scores candidates by maintenance freshness, adoption, license signal and search relevance.
- `.github/workflows/repository-scout.yml` runs the scout every Wednesday and whenever the need definitions change.
- The workflow also supports **ad-hoc searches**. Give it a GitHub search query plus a target stack and it regenerates `CANDIDATES.md`.

### How this becomes useful from ChatGPT

When a new capability is needed, use this sequence:

1. Search the existing cache first.
2. If the cache has a strong fit, use that repository as the reference/candidate.
3. If the cache has a gap, run an ad-hoc GitHub search or add a durable capability query to `needs.json`.
4. Review the top candidate for license, maintenance, security, dependency weight and overlap.
5. Integrate the winner through a project-specific branch/PR.
6. Add the winner to `repos.json` only after it earns a place.

This gives us effectively unlimited GitHub reach while keeping production stacks small and legible.
