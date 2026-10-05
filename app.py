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
    blocked = sum(bool(t["blocker"]) for t in tasks)
    c1, c2, c3 = st.columns(3)
    c1.metric("Launch tasks", total)
    c2.metric("Complete", done)
    c3.metric("With blocker", blocked)
    st.progress(done / total if total else 0)

    st.subheader("Launch gates")
    for t in tasks:
        cols = st.columns([1, 3, 1, 2])
        cols[0].write(t["area"])
        cols[1].write(t["task"])
        statuses = ["todo", "in_progress", "waiting", "founder_action", "done"]
        new_status = cols[2].selectbox(
            "Status",
            statuses,
            index=statuses.index(t["status"]),
            key=f'task_status_{t["id"]}',
            label_visibility="collapsed",
        )
        blocker = cols[3].text_input(
            "Blocker", value=t["blocker"], key=f'task_blocker_{t["id"]}', label_visibility="collapsed"
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
    with st.expander("Add supplier"):
        name = st.text_input("Supplier name")
        channel = st.text_input("Contact channel")
        flags = {}
        cols = st.columns(3)
        keys = ["blind_shipping", "private_label", "mixed_designs", "low_moq", "no_inventory_model", "sample_available"]
        for i, key in enumerate(keys):
            flags[key] = cols[i % 3].checkbox(key.replace("_", " ").title(), key=f"new_{key}")
        if st.button("Save supplier") and name.strip():
            with connect() as con:
                con.execute(
                    """INSERT OR IGNORE INTO suppliers(
                        name, contact_channel, blind_shipping, private_label, mixed_designs,
                        low_moq, no_inventory_model, sample_available
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (name.strip(), channel.strip(), *(int(flags[k]) for k in keys)),
                )
            st.rerun()

    supplier_rows = rows("SELECT * FROM suppliers ORDER BY name")
    if not supplier_rows:
        if st.button("Load safe demo suppliers"):
            seed_demo()
            st.rerun()
    for s in supplier_rows:
        sc = supplier_score(s)
        st.markdown(f"**{s['name']}** · {sc.tier} · {sc.score}/100 · {s['status']}")
        st.caption(s["notes"] or "No notes")

with tabs[2]:
    st.subheader("Product qualification")
    products = rows(
        """SELECT p.*, s.name supplier_name
           FROM products p LEFT JOIN suppliers s ON s.id=p.supplier_id
           ORDER BY p.id DESC"""
    )
    for p in products:
        econ = unit_economics(p)
        passed, missing = launch_gate(p)
        with st.container(border=True):
            st.markdown(f"**{p['name']}** · {p.get('supplier_name') or 'Unassigned'}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Retail", f"₹{float(p.get('target_retail') or 0):.0f}")
            c2.metric("Contribution", f"₹{econ['contribution']:.0f}")
            c3.metric("Margin", f"{econ['margin_pct']}%")
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
    label = st.text_input("Watch label")
    url = st.text_input("URL")
    if st.button("Add watch") and label and url:
        add_watch(label, url)
        st.rerun()
    watches = rows("SELECT * FROM watches ORDER BY id DESC")
    for w in watches:
        c1, c2 = st.columns([4, 1])
        c1.write(f"**{w['label']}**\n\n{w['url']}")
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
    if name and form:
        st.text_area("Caption", product_caption(name, form, fragrance), height=130)
        st.text_area("Product description", product_description(name, form, fragrance=fragrance), height=220)
