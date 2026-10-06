# Command Centre Importer + Decision Canon

The Command Centre is the current private operating workbook. Monakshi OS imports its current state without committing the workbook itself.

## Authority

Lower rank wins:

1. Founder locks / newest explicit founder decisions
2. Current controlling Launch Command Centre
3. Approved current operating / brand documents
4. Written supplier, customer, payment or store evidence
5. Live connected-system state
6. Current research / working notes
7. Historical / superseded material
8. Memory

Authority does not erase history. It decides which active record controls when records disagree.

## Source registry

Every material source can record:
- stable source ID
- name and type
- authority rank
- version
- private location reference
- controlling flag
- last verified date
- freshness window
- active / superseded status
- notes

Stale sources are warnings, not automatic deletions.

## Decision canon

Each decision records:
- domain
- stable decision key
- decision value
- locked / working / pending / superseded status
- source
- effective date
- rationale

A new record does **not** silently overwrite an older conflicting record.

The conflict queue surfaces multiple active values for the same decision key. The current value is resolved by:
1. source authority rank
2. locked before working within the same authority
3. newest effective date

A founder may explicitly supersede older active values.

## Command Centre XLSX import

The importer reads the actual Monakshi workbook structure:
- Master Tasks -> launch task state
- Dashboard -> high-level working decisions
- Master Task S01 -> Launch Five
- Master Task L01 -> legal-structure working assumption
- Master Task Q05 -> soft-launch shelf target

It registers the workbook as authority rank 2 and refreshes its verification timestamp.

It does not commit the workbook or raw private commercial data to Git.

## Privacy

The public repo contains schemas and code only.

The private workbook, live source registry, decision values, negotiated supplier terms and operational evidence remain in local/private state or authenticated Drive.
