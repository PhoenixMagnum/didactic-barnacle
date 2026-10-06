# House of Monakshi OS

A founder-operated command centre for House of Monakshi.

Monakshi OS is not a second storefront and does not replace Wix, the payment gateway, Instagram, Metricool, Gmail or Google Drive. It is the operating layer behind them: the place that decides what is true, what is ready, what is blocked and what requires founder action.

## V2 organization

The operating system is organized around four layers:

1. **Command** — tasks, gates, blockers, dependencies and founder actions.
2. **Memory** — source hierarchy, current decisions, evidence and superseded history.
3. **Qualification** — suppliers, candidate SKUs, testing, economics and launch readiness.
4. **Execution** — commerce, fulfilment, content, customer operations, finance and monitoring.

Read:
- [AGENTS.md](AGENTS.md) — agent roles and approval boundaries
- [Operating System](docs/MONAKSHI_OPERATING_SYSTEM.md) — complete workstream architecture
- [Source of Truth](docs/SOURCE_OF_TRUTH.md) — authority and context-hygiene rules
- [Command Centre Canon](docs/COMMAND_CENTRE_CANON.md) — controlling XLSX import, source authority and decision conflict rules
- [Workstream Map](docs/WORKSTREAMS.md) — public-safe launch map
- [Instagram + WhatsApp Supplier Bridge](docs/SOCIAL_SUPPLIER_BRIDGE.md) — multichannel identity and evidence rules
- [Evidence Ledger](docs/EVIDENCE_LEDGER.md) — provenance and conflict-preserving evidence
- [Private State Example](templates/private_state.example.json) — structure for local/private operating state

## Patterns adapted from Arindam200/awesome-ai-apps

Monakshi borrows selected patterns rather than cloning the full repository:

- task manager -> Launch Command Centre
- persistent memory -> source/decision canon
- RAG/document Q&A -> evidence vault
- human-in-the-loop -> founder gates
- web automation -> permitted monitoring
- due diligence -> supplier qualification
- financial reasoning -> unit economics
- social-media agent -> brand-consistent content
- customer support agent -> resolution workflows
- workflow audit trail -> evidence-backed status

## What the app already does

- controlling Launch Command Centre XLSX importer
- source registry with authority ranks and stale-source warnings
- decision canon that preserves conflicts and resolves the controlling value by authority
- launch command centre with explicit gates and blockers
- supplier scoring built around Monakshi's actual operating model
- one supplier identity across Instagram, WhatsApp, email, phone and website aliases
- structured evidence ledger with dated claims and source references
- stale-channel re-verification flags
- product unit economics and hard launch-readiness gates
- local document vault for supplier catalogues, terms and research
- supplier/competitor URL watchlist with change detection
- brand-safe caption and product-copy generator
- local private-state import/export
- safe demo data for a public repository

## Privacy rule

**This repository is public.**

Never commit:
- supplier negotiated rates tied to identifiable suppliers
- private supplier emails or phone numbers
- customer data
- payment data
- bank/KYC data
- private catalogues or contracts
- API tokens, OAuth credentials or secrets
- live order records

Real operating data belongs in the local SQLite database at `data/monakshi.db`, a private JSON backup, authenticated Google Drive, Gmail, Wix or the payment provider. The data directory is gitignored.

## Controlling source principle

The repository is code and operating logic, not the single factual database for the business.

Current explicit founder decisions and the current controlling Launch Command Centre outrank old trackers, historical chats and memory. See `docs/SOURCE_OF_TRUTH.md`.

## Product launch gate

A product is not launch-ready until the required evidence exists, including:
- approved physical sample
- burn-test evidence
- packaging/transit evidence
- blind-fulfilment evidence where applicable
- verified specifications
- approved photography
- commercial viability
- compliance inputs
- acceptable supplier reliability

A pretty catalogue image is not a launch gate.

## Architecture

- **Wix** remains the storefront.
- **Payment provider** remains the payment rail.
- **Instagram + Metricool** remain publishing surfaces.
- **Gmail** remains an external-communication record.
- **Google Drive** remains the private document layer.
- **Monakshi OS** owns operating truth, qualification, evidence, readiness and decision discipline.

## Run

Python 3.10+ recommended.

1. Create a virtual environment.
2. Install `requirements.txt`.
3. Run `streamlit run app.py`.

## Next engineering adapters

The next useful adapters are:
- Command Centre spreadsheet -> private state importer
- Gmail -> supplier interaction/evidence sync
- Google Drive -> private document index
- Wix -> storefront/order status sync
- Metricool/Meta -> publishing state
- payment provider -> reconciliation state

These should extend the core model rather than create parallel trackers.
