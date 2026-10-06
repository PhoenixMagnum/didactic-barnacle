# Private Gmail / Drive Ingestion Adapter

This adapter brings **explicitly selected** Gmail messages, catalogues and Drive-file extracts into local Monakshi OS evidence and search state.

It does not connect to an inbox by itself and never stores OAuth credentials.

## Why explicit selection matters

The OS should not vacuum an entire mailbox or Drive.

A selected record must identify:
- source system: gmail or drive
- external message/file ID
- entity type and canonical entity name
- date
- short subject / label
- evidence summary
- structured facts
- decision impact
- confidence
- optional private source reference
- optional source text for the local vault

## Provenance and deduplication

Every selected item receives a namespaced external ID such as:
- gmail:<message-id>
- drive:<file-id>

Duplicate detection uses:
1. external ID
2. content SHA-256 + source system + entity name

An ingestion log records metadata and hashes only. It does not store the raw email/file body.

## Redaction-safe log

Log labels and notes redact:
- email addresses
- phone-like strings
- HTTP/WWW URLs

Private raw text may exist in the local evidence/vault database if explicitly imported, but should never be committed to the public repository.

## JSON format

    {
      "records": [
        {
          "source_system": "gmail",
          "external_id": "MESSAGE_ID",
          "entity_type": "supplier",
          "entity_name": "Supplier Name",
          "artifact_type": "email",
          "occurred_at": "2026-10-06",
          "subject": "Re: wholesale enquiry",
          "source_label": "MOQ confirmation",
          "source_ref": "PRIVATE_MESSAGE_OR_DRIVE_REFERENCE",
          "summary": "Supplier confirmed MOQ 10 per design.",
          "facts": {
            "moq_per_design": 10
          },
          "decision_impact": "Not a mixed-SKU launch fit.",
          "confidence": "direct",
          "vault_text": "OPTIONAL FULL SELECTED TEXT"
        }
      ]
    }

## CLI

    PYTHONPATH=. python scripts/import_connector_evidence.py selected_records.json

The file stays private. Do not add it to Git.

## Drive files

For a Drive catalogue or quote, use source_system=drive and the Drive file ID as external_id. If text has already been extracted, pass only the selected text required for search/evidence. Keep the original private file in authenticated Drive.

## Safety boundary

The adapter:
- does not send email
- does not modify source Gmail/Drive items
- does not fetch arbitrary credentials
- does not automatically accept commercial terms
- does not commit imported source data
