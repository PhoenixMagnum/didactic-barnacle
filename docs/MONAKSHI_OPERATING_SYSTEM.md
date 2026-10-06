# House of Monakshi Operating System

## Why this exists

House of Monakshi has multiple moving surfaces: supplier sourcing, samples, testing, branding, compliance, Wix, payments, Instagram, email, fulfilment, customer support, accounting and launch decisions.

The danger is not lack of information. It is fragmented truth.

Monakshi OS turns those surfaces into one operating model.

## Architecture borrowed from Awesome AI Apps

The project adapts several useful patterns from Arindam200/awesome-ai-apps:

- task-manager agents -> Launch Command Centre
- persistent-memory agents -> project memory and decision canon
- RAG/document Q&A -> evidence vault
- human-in-the-loop agents -> founder approval gates
- browser/web automation agents -> permitted supplier/store monitoring
- due-diligence agents -> supplier qualification
- financial-reasoning agents -> unit economics and contribution
- social-media agents -> brand-consistent content
- customer-support agents -> support workflows and escalation
- workflow audit trails -> evidence-backed status changes

The repo is a pattern library. Monakshi uses the patterns, not every dependency in the library.

## The nine workstreams

### 1. Legal & Business
Owns:
- proprietor/business structure
- GST position
- bank/accounting separation
- trademark
- legal-metrology label inputs
- policies and consumer-care identity

Release gate:
No public checkout without a usable legal identity and required payment/compliance inputs.

### 2. Suppliers
Owns:
- discovery
- outreach
- qualification
- sample quote
- negotiated terms
- supplier agreement
- fulfilment annexure
- reliability history

Release gate:
No supplier becomes launch-approved without evidence for the operating model.

### 3. Products & Quality
Owns:
- candidate SKU
- sample
- physical inspection
- burn testing
- transit/packaging test
- blind-ship test
- specs
- photography
- final SKU selection

Release gate:
No product publishes merely because it looks good in a catalogue.

### 4. Brand System
Owns:
- logo
- palette
- typography
- naming
- labels
- cards
- packaging hierarchy
- supplier execution rules
- brand voice

Release gate:
One house, consistent customer experience, regardless of workshop.

### 5. Website & Commerce
Owns:
- Wix storefront
- collections
- product pages
- legal pages
- checkout
- payment provider connection
- order confirmation
- domain
- SEO basics

Release gate:
One end-to-end paid/test order must work before soft launch.

### 6. Fulfilment & Customer Operations
Owns:
- Monakshi order ID
- supplier PO link
- tracking
- shipment
- returns
- damages
- replacements
- refunds
- customer communication

Release gate:
The team must be able to trace one customer order from payment through supplier and courier to resolution.

### 7. Marketing & Audience
Owns:
- Instagram
- Metricool
- pre-launch sequence
- First Light waitlist
- photography/video briefs
- creator seeding
- launch calendar

Release gate:
Content never outruns product truth.

### 8. Finance & Analytics
Owns:
- supplier cost
- packaging/handling
- shipping
- gateway fees
- contribution
- refunds
- AOV
- conversion
- returns
- weekly KPI view

Release gate:
Products that cannot survive real landed cost do not launch.

### 9. Rehearsal & Reliability
Owns:
- fake-order rehearsal
- payment failure
- cancellation
- delayed dispatch
- damage
- replacement
- refund
- communication checks

Release gate:
No public launch until the ugly scenarios have been rehearsed.

## Source-of-truth stack

The OS must never treat every note as equal.

1. Founder locks/current explicit decisions
2. Current Launch Command Centre
3. Current approved Brand/Supplier system
4. Current supplier/customer evidence
5. Live connected-system state
6. Current research
7. Historical notes
8. Memory

See SOURCE_OF_TRUTH.md.

## Private-data boundary

This repository is public.

Do not commit:
- negotiated supplier rates tied to named suppliers
- supplier private emails/phone numbers unless already intended to be public
- private catalogues/contracts
- customer data
- payment references
- bank/KYC data
- API keys/tokens
- live order records
- confidential legal/accounting material

Private operating state belongs in:
- local gitignored SQLite/JSON
- authenticated Google Drive
- connected Gmail
- Wix/payment systems

## Current operating model

House of Monakshi is pre-launch.

The model is:
- low inventory
- supplier-held stock where commercially sensible
- blind D2C fulfilment where qualified
- private/white-label Monakshi experience
- small trial/sample stage before scale
- artistic Indian-rooted candles and objects rather than commodity catalogue dumping

The final launch shelf must be earned through testing.

## Definition of "done"

A task is not done because an email was drafted or a screen was configured.

Done requires an observable result:
- sent email has a message/thread reference
- supplier term has written evidence
- sample exists physically
- test has result/evidence
- payment checkout has successful rehearsal
- legal decision has professional/official confirmation where needed
- brand asset has version
- customer flow has been tested

## Weekly founder view

Monakshi OS should answer seven questions in under two minutes:

1. What is blocked?
2. What needs founder action?
3. Which suppliers/products are actually closest to launch?
4. Which assumptions still lack evidence?
5. What money is committed or at risk?
6. What customer-facing claim is not yet safe to make?
7. What are the three highest-leverage actions now?

If the system cannot answer those, it is decoration rather than operations.
