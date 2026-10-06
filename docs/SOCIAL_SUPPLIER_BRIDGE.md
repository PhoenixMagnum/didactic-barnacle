# Instagram + WhatsApp Supplier Bridge

Supplier conversations often begin on Instagram, move to WhatsApp and later produce an email, invoice, catalogue or sample.

Monakshi OS treats that as **one supplier with several channels**, not several suppliers.

## Data model

### Supplier
The canonical business identity.

### Channel
A place where Monakshi communicates with that supplier:
- Instagram
- WhatsApp
- email
- phone
- website
- other

Each channel can record:
- handle / number alias
- profile URL
- active / inactive / unverified status
- whether it is the primary route
- last verified date
- operational notes

### Alias
A deduplication key that maps alternate names, handles, phone numbers or email aliases back to the canonical supplier.

Examples:
- supplier display name
- @instagram_handle
- WhatsApp number
- email address
- catalogue trading name

### Evidence
A dated claim from a channel or document.

Examples:
- MOQ 10/design
- mixed trial accepted
- private label available
- neutral parcel confirmed
- direct dispatch available
- supplier-held stock accepted
- dispatch SLA 1–3 days
- replacement terms

Evidence preserves history. A later WhatsApp message can supersede an older Instagram statement without deleting the earlier evidence.

## Privacy boundary

Do not commit raw DMs, phone numbers, private emails, screenshots or negotiated terms to this public repository.

Raw evidence stays in Drive / source apps. The local private state stores only the minimum structured facts and private source references needed to audit decisions.

## Current ingestion modes

1. **Direct connected source**, when an authorized reliable connector exists.
2. **Private export/import**, for structured JSON or exported conversation data.
3. **Manual evidence capture**, for a message or screenshot reviewed by the founder.

The system must never claim live Instagram or WhatsApp synchronization when no authorized connector exists.

## Freshness

Social supplier terms decay quickly, especially around festive production windows.

A channel with no verified date, or one older than the configured freshness window, is marked for re-verification. Stale evidence remains history but should not control a new purchase without confirmation.

## Human gate

The bridge can organize and extract evidence. It does not autonomously send DMs, agree to terms, place orders or make payments.
