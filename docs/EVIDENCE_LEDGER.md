# Evidence Ledger

Monakshi OS separates **claims** from **evidence**.

A supplier score or operating decision should not depend on a remembered chat fragment. The evidence ledger stores a short structured record of what was said, when, by which source, and how it changes a decision.

## Evidence record

Each record can contain:

- entity type and entity name
- source type such as Gmail, catalogue, WhatsApp, website, lab reply or manual inspection
- a private source reference
- timestamp and subject
- concise summary
- structured facts
- decision impact
- confidence: direct, derived or unverified

## Privacy

Never commit raw supplier emails, customer messages, phone numbers, addresses, credentials or private contracts to this public repository.

Keep those source materials in Gmail, Drive or another authenticated private system. The local evidence ledger should contain only the minimum structured facts needed to make and audit business decisions.

## Conflict rule

When evidence conflicts, do not silently overwrite history.

Keep both records. Prefer the newest direct evidence for the current operating decision unless a later author/founder decision explicitly overrides it.

Example:

- Earlier supplier reply: mixed-SKU trials available.
- Later supplier reply during Diwali rush: MOQ 100 per SKU, no samples until post-Christmas.

Both remain in the ledger. The later statement controls the launch window.

## Import

A full private-state backup may include an `evidence` array and will import through the Streamlit Command Centre.

Evidence-only JSON can also be imported with:

    PYTHONPATH=. python scripts/import_evidence.py private_evidence.json

The private JSON belongs outside Git.
