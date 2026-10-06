from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json

import streamlit as st

from monakshi_os.channels import add_alias, add_channel, channel_is_stale, supplier_aliases, supplier_channels
from monakshi_os.command_centre import import_command_centre
from monakshi_os.db import connect, init_db, rows
from monakshi_os.evidence import entity_facts, search_evidence, upsert_evidence
from monakshi_os.ingestion import ingest_connector_records, ingestion_log
from monakshi_os.muse import product_caption, product_description
from monakshi_os.scoring import launch_gate, supplier_score, unit_economics
from monakshi_os.rehearsal import evaluate_launch, render_markdown
from monakshi_os.scout import add_watch, check_watch
from monakshi_os.seed import seed_demo
from monakshi_os.state_io import export_state, import_state
from monakshi_os.source_canon import (
    decision_canon,
    decision_conflicts,
    resolve_current_decision,
    source_is_stale,
    source_registry,
    upsert_decision,
    upsert_source,
)
from monakshi_os.vault import ingest, search

st.set_page_config(page_title="House of Monakshi OS", page_icon="🪔", layout="wide")
init_db()

st.title("House of Monakshi OS")
st.caption("Operations brain for sourcing, qualification, launch gates and brand consistency. Keep confidential data local/private.")

tabs = st.tabs(["Command Centre", "Suppliers", "Channels", "Products", "Evidence", "Vault", "Watchtower", "Muse", "Canon"])

with tabs[0]:
    tasks = rows("SELECT * FROM launch_tasks ORDER BY area, id")
    total = len(tasks)
    done = sum(t["status"] == "done" for t in tasks)
    waiting = sum(t["status"] == "waiting" for t in tasks)
    blocked = sum(bool(t["blocker"]) for t in tasks)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Launch tasks", total)
    c2.metric("Complete", done)
    c3.metric("Waiting", waiting)
    c4.metric("With blocker", blocked)
    st.progress(done / total if total else 0)

    rehearsal = evaluate_launch()
    if rehearsal["decision"] == "GO":
        st.success("Launch firewall: GO")
    else:
        st.error(f"Launch firewall: NO-GO · {len(rehearsal['blocking_gates'])} hard gate(s) still open")
        with st.expander("Show hard launch blockers"):
            for gate in rehearsal["blocking_gates"]:
                st.write(f"**{gate['key']} · {gate['label']}** — {gate['detail']}")
    st.download_button(
        "Download launch rehearsal report",
        data=render_markdown(rehearsal),
        file_name="house_of_monakshi_launch_rehearsal.md",
        mime="text/markdown",
    )

    with st.expander("Controlling Command Centre import", expanded=False):
        st.caption("Imports the private controlling XLSX into local Monakshi OS state. The workbook itself is not committed to Git.")
        command_file = st.file_uploader(
            "Import current Launch Command Centre (.xlsx)",
            type=["xlsx"],
            key="command_centre_xlsx",
        )
        if command_file and st.button("Import controlling Command Centre"):
            result = import_command_centre(
                command_file.getvalue(),
                filename=command_file.name,
                source_location="PRIVATE_UPLOAD",
            )
            st.success(
                f"Imported {result['tasks']} master tasks and {result['decisions']} controlling decisions from {result['version'] or command_file.name}."
            )
            st.rerun()

    with st.expander("Private state import / export", expanded=False):
        st.caption("Imports write only to your local SQLite database. Do not commit the generated database or private JSON to this public repository.")
        state_file = st.file_uploader("Import Monakshi private state JSON", type=["json"], key="private_state_json")
        if state_file and st.button("Import private state"):
            payload = json.loads(state_file.getvalue().decode("utf-8"))
            counts = import_state(payload)
            st.success(
                f"Imported {counts.get('sources', 0)} sources, {counts.get('decisions', 0)} decisions, {counts['launch_tasks']} tasks, {counts['suppliers']} suppliers, {counts.get('channels', 0)} channels, {counts.get('aliases', 0)} aliases, {counts['products']} products, {counts.get('evidence', 0)} evidence records and {counts.get('ingestions', 0)} ingestion-log rows."
            )
            st.rerun()
        snapshot = json.dumps(export_state(), ensure_ascii=False, indent=2, default=str)
        st.download_button(
            "Export local state backup",
            data=snapshot,
            file_name="monakshi_private_state_backup.json",
            mime="application/json",
        )

    st.subheader("Launch gates")
    statuses = ["todo", "in_progress", "waiting", "founder_action", "blocked", "done"]
    for t in tasks:
        cols = st.columns([1, 3, 1.3, 2])
        cols[0].write(t["area"])
        cols[1].write(t["task"])
        new_status = cols[2].selectbox(
            "Status",
            statuses,
            index=statuses.index(t["status"]),
            key=f'task_status_{t["id"]}',
            label_visibility="collapsed",
        )
        blocker = cols[3].text_input(
            "Blocker",
            value=t["blocker"],
            key=f'task_blocker_{t["id"]}',
            label_visibility="collapsed",
            placeholder="Blocker / dependency",
        )
        if new_status != t["status"] or blocker != t["blocker"]:
            with connect() as con:
                con.execute(
                    "UPDATE launch_tasks SET status=?, blocker=? WHERE id=?",
                    (new_status, blocker, t["id"]),
                )
            st.rerun()

with tabs[1]:
    st.subheader("Supplier intelligence")

    with st.expander("Add supplier", expanded=False):
        name = st.text_input("Supplier name")
        channel = st.text_input("Contact channel")
        status = st.selectbox("Pipeline status", ["discovered", "contacted", "replied", "sampling", "testing", "approved", "paused"])
        flag_keys = ["blind_shipping", "private_label", "mixed_designs", "low_moq", "no_inventory_model", "sample_available"]
        flag_cols = st.columns(3)
        flags = {}
        for i, key in enumerate(flag_keys):
            flags[key] = flag_cols[i % 3].checkbox(key.replace("_", " ").title(), key=f"new_{key}")
        score_cols = st.columns(4)
        quality = score_cols[0].number_input("Quality", 0.0, 10.0, 0.0, 0.5)
        aesthetic = score_cols[1].number_input("Aesthetic", 0.0, 10.0, 0.0, 0.5)
        commercial = score_cols[2].number_input("Commercial", 0.0, 10.0, 0.0, 0.5)
        reliability = score_cols[3].number_input("Reliability", 0.0, 10.0, 0.0, 0.5)
        notes = st.text_area("Notes")
        if st.button("Save supplier") and name.strip():
            with connect() as con:
                con.execute(
                    """INSERT OR IGNORE INTO suppliers(
                        name, contact_channel, status, blind_shipping, private_label, mixed_designs,
                        low_moq, no_inventory_model, sample_available, quality_score,
                        aesthetic_score, commercial_score, reliability_score, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        name.strip(), channel.strip(), status,
                        *(int(flags[k]) for k in flag_keys),
                        quality, aesthetic, commercial, reliability, notes.strip(),
                    ),
                )
            st.rerun()

    supplier_rows = rows("SELECT * FROM suppliers ORDER BY name")
    if not supplier_rows:
        st.info("No suppliers in the local database yet.")
        if st.button("Load safe demo suppliers"):
            seed_demo()
            st.rerun()

    for s in supplier_rows:
        sc = supplier_score(s)
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**{s['name']}**")
            c2.metric("Tier", sc.tier)
            c3.metric("Score", f"{sc.score}/100")
            st.caption(f"{s['status']} · {s['contact_channel'] or 'channel not set'}")
            st.write(s["notes"] or "No notes")
            st.caption(
                "Blind ship: {0} · Private label: {1} · Low MOQ: {2} · No-inventory: {3}".format(
                    "yes" if s["blind_shipping"] else "no",
                    "yes" if s["private_label"] else "no",
                    "yes" if s["low_moq"] else "no",
                    "yes" if s["no_inventory_model"] else "no",
                )
            )

with tabs[2]:
    st.subheader("Supplier channels")
    st.caption("One supplier can have Instagram, WhatsApp, email, phone and website routes. Channels are evidence routes, not separate supplier identities.")

    channel_suppliers = rows("SELECT id, name FROM suppliers ORDER BY name")
    channel_supplier_map = {s["name"]: s["id"] for s in channel_suppliers}

    if channel_supplier_map:
        with st.expander("Add or update a channel", expanded=False):
            supplier_name = st.selectbox("Supplier", list(channel_supplier_map), key="channel_supplier")
            channel_type = st.selectbox(
                "Channel type",
                ["instagram", "whatsapp", "email", "phone", "website", "other"],
                key="channel_type",
            )
            handle = st.text_input("Handle / number / address", key="channel_handle")
            profile_url = st.text_input("Profile / source URL", key="channel_url")
            channel_status = st.selectbox("Channel status", ["active", "unverified", "inactive"], key="channel_status")
            last_verified = st.text_input("Last verified", placeholder="YYYY-MM-DD", key="channel_verified")
            primary = st.checkbox("Primary contact route", key="channel_primary")
            channel_notes = st.text_area("Channel notes", key="channel_notes")
            if st.button("Save channel"):
                add_channel(
                    supplier_id=channel_supplier_map[supplier_name],
                    channel_type=channel_type,
                    handle=handle,
                    profile_url=profile_url,
                    status=channel_status,
                    is_primary=primary,
                    last_verified_at=last_verified,
                    notes=channel_notes,
                )
                st.rerun()

        with st.expander("Add supplier alias", expanded=False):
            alias_supplier = st.selectbox("Canonical supplier", list(channel_supplier_map), key="alias_supplier")
            alias_type = st.selectbox(
                "Alias type",
                ["name", "instagram", "whatsapp", "email", "catalogue", "other"],
                key="alias_type",
            )
            alias = st.text_input("Alias / handle / number", key="alias_value")
            if st.button("Save alias") and alias.strip():
                add_alias(channel_supplier_map[alias_supplier], alias, alias_type)
                st.rerun()
    else:
        st.info("Add suppliers before adding channels.")

    channel_rows = supplier_channels()
    if channel_rows:
        for c in channel_rows:
            with st.container(border=True):
                cols = st.columns([2.6, 1.3, 2.2, 1.2])
                cols[0].markdown(f"**{c['supplier_name']}**")
                cols[1].write(c["channel_type"].title())
                cols[2].write(c["handle"] or c["profile_url"] or "Route recorded")
                freshness = "RE-VERIFY" if channel_is_stale(c.get("last_verified_at")) else "CURRENT"
                cols[3].write(freshness)
                bits = [c.get("status"), "primary" if c.get("is_primary") else "", c.get("last_verified_at")]
                st.caption(" · ".join(str(x) for x in bits if x))
                if c.get("notes"):
                    st.write(c["notes"])
    else:
        st.info("No channel routes in the local private state yet.")

    alias_rows = supplier_aliases()
    if alias_rows:
        with st.expander("Alias map"):
            for alias_row in alias_rows:
                st.write(f"{alias_row['alias']} ({alias_row['alias_type']}) → {alias_row['supplier_name']}")

with tabs[3]:
    st.subheader("Product qualification")

    suppliers = rows("SELECT id, name FROM suppliers ORDER BY name")
    supplier_map = {s["name"]: s["id"] for s in suppliers}

    with st.expander("Add candidate SKU", expanded=False):
        if not supplier_map:
            st.info("Add a supplier first.")
        else:
            supplier_name = st.selectbox("Supplier", list(supplier_map))
            product_name = st.text_input("Product name")
            category = st.text_input("Category", placeholder="Urli, floral, mithai, diya...")
            pcols = st.columns(4)
            supplier_price = pcols[0].number_input("Supplier price ₹", 0.0, step=10.0)
            target_retail = pcols[1].number_input("Target retail ₹", 0.0, step=10.0)
            shipping_cost = pcols[2].number_input("Shipping ₹", 0.0, step=10.0)
            packaging_cost = pcols[3].number_input("Packaging ₹", 0.0, step=5.0)
            payment_fee_pct = st.number_input("Payment fee %", 0.0, 15.0, 2.0, 0.1)
            if st.button("Save candidate SKU") and product_name.strip():
                with connect() as con:
                    con.execute(
                        """INSERT OR IGNORE INTO products(
                            supplier_id, name, category, supplier_price, target_retail,
                            shipping_cost, packaging_cost, payment_fee_pct
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            supplier_map[supplier_name], product_name.strip(), category.strip(),
                            supplier_price, target_retail, shipping_cost, packaging_cost, payment_fee_pct,
                        ),
                    )
                st.rerun()

    products = rows(
        """SELECT p.*, s.name supplier_name
           FROM products p LEFT JOIN suppliers s ON s.id=p.supplier_id
           ORDER BY p.id DESC"""
    )
    if not products:
        st.info("No candidate SKUs yet.")

    for p in products:
        econ = unit_economics(p)
        passed, missing = launch_gate(p)
        with st.container(border=True):
            st.markdown(f"**{p['name']}** · {p.get('supplier_name') or 'Unassigned'} · {p['category'] or 'uncategorized'}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Supplier", f"₹{float(p.get('supplier_price') or 0):.0f}")
            c2.metric("Retail", f"₹{float(p.get('target_retail') or 0):.0f}")
            c3.metric("Contribution", f"₹{econ['contribution']:.0f}")
            c4.metric("Margin", f"{econ['margin_pct']}%")

            gate_cols = st.columns(5)
            sample = gate_cols[0].checkbox("Sample", value=p["sample_status"] in {"approved", "passed"}, key=f'sample_{p["id"]}')
            burn = gate_cols[1].checkbox("Burn", value=bool(p["burn_test_pass"]), key=f'burn_{p["id"]}')
            packaging = gate_cols[2].checkbox("Pack", value=bool(p["packaging_test_pass"]), key=f'pack_{p["id"]}')
            photo = gate_cols[3].checkbox("Photo", value=bool(p["photo_approved"]), key=f'photo_{p["id"]}')
            specs = gate_cols[4].checkbox("Specs", value=bool(p["specs_verified"]), key=f'specs_{p["id"]}')

            if (
                sample != (p["sample_status"] in {"approved", "passed"})
                or burn != bool(p["burn_test_pass"])
                or packaging != bool(p["packaging_test_pass"])
                or photo != bool(p["photo_approved"])
                or specs != bool(p["specs_verified"])
            ):
                with connect() as con:
                    con.execute(
                        """UPDATE products SET sample_status=?, burn_test_pass=?, packaging_test_pass=?,
                           photo_approved=?, specs_verified=? WHERE id=?""",
                        ("approved" if sample else "not_requested", int(burn), int(packaging), int(photo), int(specs), p["id"]),
                    )
                st.rerun()

            if passed:
                st.success("Launch gate passed")
            else:
                st.warning("Not launch ready: " + ", ".join(missing))


with tabs[4]:
    st.subheader("Evidence ledger")
    st.caption("Structured provenance for supplier, lab, website and operational claims. Keep raw private messages outside Git.")

    with st.expander("Import selected Gmail / Drive evidence", expanded=False):
        st.caption("Import only records you explicitly selected/exported. The adapter deduplicates by source ID and content hash, redacts the ingestion log, and can index selected text into the private vault.")
        connector_file = st.file_uploader(
            "Selected connector evidence JSON",
            type=["json"],
            key="connector_evidence_json",
        )
        if connector_file and st.button("Import selected connector evidence"):
            try:
                connector_payload = json.loads(connector_file.getvalue().decode("utf-8"))
                connector_records = (
                    connector_payload.get("records", [])
                    if isinstance(connector_payload, dict)
                    else connector_payload
                )
                if not isinstance(connector_records, list):
                    raise ValueError("Expected a list of records or an object containing a records list.")
                connector_result = ingest_connector_records(connector_records)
            except (json.JSONDecodeError, ValueError) as exc:
                st.error(f"Could not import connector evidence: {exc}")
            else:
                st.success(
                    f"Selected {connector_result['selected']} · imported {connector_result['imported']} · "
                    f"duplicates skipped {connector_result['duplicates']} · vault chunks {connector_result['vault_chunks']}."
                )
                st.rerun()

    evidence_suppliers = [s["name"] for s in rows("SELECT name FROM suppliers ORDER BY name")]
    if evidence_suppliers:
        with st.expander("Capture Instagram / WhatsApp / other evidence", expanded=False):
            ev_supplier = st.selectbox("Supplier", evidence_suppliers, key="ev_supplier")
            ev_source = st.selectbox(
                "Source",
                ["instagram", "whatsapp", "email", "catalogue", "website", "phone", "inspection", "other"],
                key="ev_source",
            )
            ev_when = st.text_input("Message / evidence date", placeholder="YYYY-MM-DD or ISO timestamp", key="ev_when")
            ev_subject = st.text_input("Short label", placeholder="MOQ / blind fulfilment confirmation", key="ev_subject")
            ev_summary = st.text_area("What the supplier actually confirmed", key="ev_summary")
            ev_facts = st.text_area(
                "Structured facts JSON (optional)",
                placeholder='{"moq_per_design": 10, "blind_shipping": true}',
                key="ev_facts",
            )
            ev_impact = st.text_area("Decision impact / next action", key="ev_impact")
            ev_confidence = st.selectbox("Confidence", ["direct", "derived", "unverified"], key="ev_confidence")
            ev_ref = st.text_input("Private source reference", placeholder="Drive file, screenshot name, thread/date", key="ev_ref")
            if st.button("Save evidence") and ev_summary.strip():
                try:
                    parsed_facts = json.loads(ev_facts) if ev_facts.strip() else {}
                    if not isinstance(parsed_facts, dict):
                        raise ValueError("Facts must be a JSON object.")
                except (json.JSONDecodeError, ValueError) as exc:
                    st.error(f"Invalid facts JSON: {exc}")
                else:
                    upsert_evidence(
                        {
                            "entity_type": "supplier",
                            "entity_name": ev_supplier,
                            "source_type": ev_source,
                            "source_label": ev_subject,
                            "source_ref": ev_ref,
                            "occurred_at": ev_when,
                            "subject": ev_subject,
                            "summary": ev_summary,
                            "facts": parsed_facts,
                            "decision_impact": ev_impact,
                            "confidence": ev_confidence,
                        }
                    )
                    st.rerun()

    eq = st.text_input("Search evidence", key="evidence_search")
    supplier_names = [s["name"] for s in rows("SELECT name FROM suppliers ORDER BY name")]
    entity_filter = st.selectbox("Filter entity", ["All"] + supplier_names, key="evidence_entity")
    evidence_rows = search_evidence(
        query=eq,
        entity_name="" if entity_filter == "All" else entity_filter,
    )
    st.metric("Evidence records", len(evidence_rows))
    for ev in evidence_rows:
        with st.container(border=True):
            st.markdown(f"**{ev['entity_name']}** · {ev['source_type']} · {ev['confidence']}")
            if ev.get("subject"):
                st.caption(ev["subject"])
            st.write(ev["summary"])
            facts = ev.get("facts", {})
            if facts:
                st.json(facts)
            if ev.get("decision_impact"):
                st.info("Decision impact: " + ev["decision_impact"])
            source_bits = [x for x in [ev.get("source_label"), ev.get("occurred_at")] if x]
            if source_bits:
                st.caption(" · ".join(source_bits))

    if entity_filter != "All":
        facts = entity_facts(entity_filter)
        if facts:
            with st.expander("Consolidated fact history"):
                st.json(facts)

    logs = ingestion_log()
    if logs:
        with st.expander("Private ingestion log"):
            st.caption("Metadata and hashes only. Raw connector bodies are not written into this log.")
            for log in logs[:100]:
                st.write(
                    f"{log['source_system']} · {log['entity_name']} · {log['artifact_type']} · "
                    f"{log['status']} · {log.get('redacted_label') or 'record'}"
                )
                st.caption(f"{log.get('occurred_at') or 'undated'} · {log['external_id']}")

with tabs[5]:
    st.subheader("Supplier & product document vault")
    upload = st.file_uploader("Add a PDF, TXT, MD or CSV", type=["pdf", "txt", "md", "csv"])
    if upload and st.button("Ingest document"):
        Path("data/uploads").mkdir(parents=True, exist_ok=True)
        target = Path("data/uploads") / Path(upload.name).name
        target.write_bytes(upload.getvalue())
        count = ingest(target)
        st.success(f"Indexed {count} chunks from {upload.name}")

    q = st.text_input("Search the vault")
    if q:
        results = search(q)
        if not results:
            st.info("No matching evidence found.")
        for r in results:
            st.markdown(f"**{r['citation']}**")
            st.write(r["content"][:900])

with tabs[6]:
    st.subheader("Supplier / competitor page watchtower")
    st.caption("Use only on pages you are allowed to access. This v1 checks public page text for change.")
    label = st.text_input("Watch label")
    url = st.text_input("URL")
    if st.button("Add watch") and label and url:
        add_watch(label, url)
        st.rerun()

    watches = rows("SELECT * FROM watches ORDER BY id DESC")
    for w in watches:
        c1, c2 = st.columns([4, 1])
        c1.write(f"**{w['label']}**\n\n{w['url']}")
        if w["last_checked_at"]:
            c1.caption(f"Last checked: {w['last_checked_at']}")
        if c2.button("Check now", key=f'watch_{w["id"]}'):
            try:
                result = check_watch(w["id"])
                st.success("Change detected" if result["changed"] else "No change detected")
            except Exception as exc:
                st.error(str(exc))

with tabs[7]:
    st.subheader("Monakshi Muse")
    name = st.text_input("Product name", key="muse_name")
    form = st.text_input("Form / inspiration", placeholder="lotus pond urli", key="muse_form")
    fragrance = st.text_input("Fragrance", key="muse_fragrance")
    occasion = st.text_input("Occasion", key="muse_occasion")
    if name and form:
        st.text_area("Caption", product_caption(name, form, fragrance, occasion), height=130)
        st.text_area("Product description", product_description(name, form, fragrance=fragrance), height=220)


with tabs[8]:
    st.subheader("Source & decision canon")
    st.caption("This is the context firewall: current founder decisions outrank the Command Centre, which outranks operating documents, evidence, research and historical material.")

    sources = source_registry()
    decisions = decision_canon()
    conflicts = decision_conflicts()

    c1, c2, c3 = st.columns(3)
    c1.metric("Registered sources", len(sources))
    c2.metric("Active decisions", sum(d["status"] in {"locked", "working"} for d in decisions))
    c3.metric("Decision conflicts", len(conflicts))

    with st.expander("Record founder decision", expanded=False):
        domain = st.text_input("Domain", value="general", key="canon_domain")
        decision_key = st.text_input("Decision key", placeholder="primary_gateway", key="canon_key")
        decision_value = st.text_area("Decision", key="canon_value")
        decision_status = st.selectbox("Status", ["locked", "working", "pending"], key="canon_status")
        rationale = st.text_area("Rationale / context", key="canon_rationale")
        supersede = st.checkbox(
            "Explicitly supersede prior active decisions with this key",
            value=False,
            key="canon_supersede",
        )
        if st.button("Save founder decision") and decision_key.strip() and decision_value.strip():
            now = datetime.now(timezone.utc).isoformat()
            upsert_source(
                {
                    "source_id": "founder-current",
                    "name": "Current explicit founder decisions",
                    "source_type": "founder",
                    "authority_rank": 1,
                    "version": "current",
                    "location": "Monakshi OS",
                    "is_controlling": True,
                    "last_verified_at": now,
                    "freshness_days": 3650,
                    "status": "active",
                    "notes": "Explicit decisions entered by the founder.",
                }
            )
            decision_id = f"founder:{decision_key.strip()}:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            upsert_decision(
                {
                    "decision_id": decision_id,
                    "domain": domain.strip() or "general",
                    "decision_key": decision_key.strip(),
                    "decision_value": decision_value.strip(),
                    "status": decision_status,
                    "source_id": "founder-current",
                    "effective_date": now,
                    "rationale": rationale.strip(),
                },
                supersede_prior=supersede,
            )
            st.rerun()

    if conflicts:
        st.error(f"{len(conflicts)} active decision conflict(s) need review.")
        for conflict in conflicts:
            with st.container(border=True):
                st.markdown(f"**{conflict['decision_key']}**")
                current = conflict.get("current")
                if current:
                    st.write(f"Current by authority: {current['decision_value']}")
                    st.caption(f"{current.get('source_name') or current.get('source_id')} · rank {current.get('authority_rank')}")
                for record in conflict["records"]:
                    st.write(
                        f"- {record['decision_value']} · {record['status']} · "
                        f"{record.get('source_name') or record.get('source_id') or 'no source'}"
                    )
    else:
        st.success("No active decision contradictions detected.")

    st.markdown("### Source registry")
    if not sources:
        st.info("No sources registered yet. Import the controlling Command Centre or private state.")
    for source in sources:
        with st.container(border=True):
            cols = st.columns([3, 1, 1, 1.4])
            cols[0].markdown(f"**{source['name']}**")
            cols[1].write(f"Rank {source['authority_rank']}")
            cols[2].write(source.get("version") or "—")
            cols[3].write("STALE" if source_is_stale(source) else "CURRENT")
            st.caption(
                " · ".join(
                    str(x) for x in [
                        source.get("source_type"),
                        "controlling" if source.get("is_controlling") else "",
                        source.get("last_verified_at"),
                        source.get("status"),
                    ] if x
                )
            )
            if source.get("notes"):
                st.write(source["notes"])

    st.markdown("### Decision canon")
    if not decisions:
        st.info("No decisions recorded yet.")
    for decision in decisions:
        with st.container(border=True):
            current = resolve_current_decision(decision["decision_key"])
            is_current = bool(current and current["decision_id"] == decision["decision_id"])
            label = "CURRENT" if is_current else decision["status"].upper()
            st.markdown(f"**{decision['decision_key']}** · {label}")
            st.write(decision["decision_value"])
            st.caption(
                f"{decision.get('domain') or 'general'} · "
                f"{decision.get('source_name') or decision.get('source_id') or 'no source'} · "
                f"effective {decision.get('effective_date') or 'undated'}"
            )
            if decision.get("rationale"):
                st.write(decision["rationale"])
