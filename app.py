from __future__ import annotations

from pathlib import Path

import streamlit as st

from monakshi_os.db import connect, init_db, rows
from monakshi_os.muse import product_caption, product_description
from monakshi_os.scoring import launch_gate, supplier_score, unit_economics
from monakshi_os.scout import add_watch, check_watch
from monakshi_os.seed import seed_demo
from monakshi_os.vault import ingest, search

st.set_page_config(page_title="House of Monakshi OS", page_icon="🪔", layout="wide")
init_db()

st.title("House of Monakshi OS")
st.caption("Operations brain for sourcing, qualification, launch gates and brand consistency. Keep confidential data local/private.")

tabs = st.tabs(["Command Centre", "Suppliers", "Products", "Vault", "Watchtower", "Muse"])

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

    st.subheader("Launch gates")
    statuses = ["todo", "in_progress", "waiting", "founder_action", "done"]
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

with tabs[3]:
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

with tabs[4]:
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

with tabs[5]:
    st.subheader("Monakshi Muse")
    name = st.text_input("Product name", key="muse_name")
    form = st.text_input("Form / inspiration", placeholder="lotus pond urli", key="muse_form")
    fragrance = st.text_input("Fragrance", key="muse_fragrance")
    occasion = st.text_input("Occasion", key="muse_occasion")
    if name and form:
        st.text_area("Caption", product_caption(name, form, fragrance, occasion), height=130)
        st.text_area("Product description", product_description(name, form, fragrance=fragrance), height=220)
