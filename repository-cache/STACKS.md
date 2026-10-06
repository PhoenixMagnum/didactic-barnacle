# Stack Map

## S0 — Repository intelligence

**Status:** ACTIVE

- `Arindam200/awesome-ai-apps`
- `f/prompts.chat`
- `mattpocock/skills`
- `mcp-finder/awesome-mcp-servers`
- `ripienaar/free-for-dev`

**Rule:** Discovery feeds the cache. It does not automatically change production architecture.

## S1 — Monakshi independent storefront

**Status:** ACTIVE

- `vercel/next.js`
- `tailwindlabs/tailwindcss`
- `shadcn-ui/ui`
- `GrapesJS/grapesjs`
- `supabase/supabase`
- `razorpay/razorpay-node`
- `resend/react-email`
- `resend/resend-node`

**Rule:** This is the controlling web stack. Commerce reference repos are reference-only unless a concrete gap appears.

## S2 — Monakshi operations + automation

**Status:** ACTIVE

- `ComposioHQ/composio`
- `n8n-io/n8n`
- `microsoft/playwright`
- `dgtlmoon/changedetection.io`
- `firecrawl/firecrawl`
- `twentyhq/twenty`
- `listmonk/listmonk`
- `PostHog/posthog`

**Rule:** Prefer existing ChatGPT connectors first; add self-hosted automation only when it removes recurring manual work or creates a durable audit trail.

## S3 — StoryVault writing + publishing

**Status:** ACTIVE_CONSERVATIVE

- `jgm/pandoc`
- `microsoft/markitdown`
- `languagetool-org/languagetool`
- `Sigil-Ebook/Sigil`
- `kovidgoyal/calibre`
- `kevboh/longform`
- `obsidianmd/obsidian-api`

**Rule:** Obsidian/StoryVault remains local-first, deterministic and dependency-light. Longform is optional; external memory and agent swarms never become canon authorities.

## S4 — Research + knowledge processing

**Status:** READY_WHEN_NEEDED

- `zotero/zotero`
- `microsoft/markitdown`
- `docling-project/docling`
- `paperless-ngx/paperless-ngx`
- `infiniflow/ragflow`
- `onyx-dot-app/onyx`
- `khoj-ai/khoj`

**Rule:** Evidence and source provenance outrank convenience. RAG layers are optional accelerators, not sources of truth.

## S5 — ChatGPT / agent engineering lab

**Status:** REFERENCE_FIRST

- `openai/openai-cookbook`
- `openai/codex`
- `ComposioHQ/composio`
- `modelcontextprotocol/servers`
- `langchain-ai/langgraph`
- `langfuse/langfuse`
- `BerriAI/litellm`
- `topoteretes/cognee`
- `mem0ai/mem0`

**Rule:** Use this stack to prototype bounded agents and integrations. Do not import experimental autonomy into StoryVault canon or Monakshi production without an explicit use case.

## S6 — Learning + future infrastructure

**Status:** LIBRARY

- `sindresorhus/awesome`
- `awesome-selfhosted/awesome-selfhosted`
- `public-apis/public-apis`
- `ripienaar/free-for-dev`
- `EbookFoundation/free-programming-books`
- `metabase/metabase`
- `nocodb/nocodb`
- `makeplane/plane`

**Rule:** Reference shelf only until a concrete requirement promotes an item into another stack.


## Promotion logic

- **P0** repos may be used when the relevant active project needs them.
- **P1** repos are preferred candidates for the next matching capability gap.
- **P2** repos should remain references until a requirement justifies adoption.
- **P3** repos stay quarantined from production by default.

When two repositories overlap, prefer the one already present in an active stack. A new repo must beat the incumbent on at least one material dimension: reliability, simplicity, cost, privacy, maintainability, interoperability, or capability.
