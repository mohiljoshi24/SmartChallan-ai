"""
SmartChallan AI - Page 2: E-Challan Registry & Evidence Vault
Central repository of legal traffic citations, court-admissible photographic evidence,
PDF generation/download, and digital dispatch status.
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime

from core.database import (
    get_all_violations,
    get_violation_by_id,
    update_violation_status,
    sync_to_csv,
    CSV_PATH
)
from core.challan_generator import generate_challan_pdf

st.set_page_config(page_title="E-Challan Registry — SmartChallan AI", page_icon="📑", layout="wide")

st.markdown("## 📑 Official E-Challan Registry & Evidence Vault")
st.caption("Centralized Court-Admissible Traffic Citations • Tripartite Photographic Proof • Direct PDF Dispatch")

# Search and Filter Toolbar
col_search, col_filter, col_export = st.columns([4, 3, 2])
with col_search:
    search_query = st.text_input("🔍 Search by Registration Plate or Challan ID:", placeholder="e.g. MH 12, KA 03, CH-2026")
with col_filter:
    status_filter = st.selectbox("Filter by Status:", ["All", "Issued", "Paid", "Pending Review", "Contested"])
with col_export:
    st.write("")
    st.write("")
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "rb") as f:
            st.download_button("📥 Export CSV Audit Log", f.read(), "smartchallan_violations.csv", "text/csv", use_container_width=True)

# Fetch Violations
all_violations = get_all_violations(status_filter=status_filter if status_filter != "All" else None)

# Apply text search filter
if search_query:
    q = search_query.strip().upper()
    filtered_violations = [
        v for v in all_violations
        if q in v["plate_number"].upper() or q in v["challan_id"].upper()
    ]
else:
    filtered_violations = all_violations

st.markdown(f"**Found {len(filtered_violations)} violation record(s)**")

# Main Layout: Master-Detail view
col_list, col_detail = st.columns([5, 6])

with col_list:
    st.subheader("📋 Registered Citations")
    if not filtered_violations:
        st.info("No matching records found in registry.")
        selected_challan_id = None
    else:
        # Create a nice selection radio or dataframe
        challan_options = [f"{v['challan_id']} | {v['plate_number']} ({v['status']})" for v in filtered_violations]
        selected_option = st.radio(
            "Select Citation to Inspect Evidence:",
            challan_options,
            label_visibility="collapsed"
        )
        selected_challan_id = selected_option.split(" | ")[0]

with col_detail:
    st.subheader("🔍 Case Evidence Inspector")

    if selected_challan_id:
        record = get_violation_by_id(selected_challan_id)
        if record:
            # Header Box
            st.markdown(f"### Citation #{record['challan_id']}")

            # Status Badge
            status = record["status"]
            if status == "Paid":
                st.success("🟢 STATUS: PAID & CLEARED")
            elif status == "Issued":
                st.error("🔴 STATUS: ISSUED (UNPAID - 60 DAYS STATUTORY WINDOW)")
            elif status == "Pending Review":
                st.warning("🟡 STATUS: PENDING OFFICER VERIFICATION")
            else:
                st.info(f"🔵 STATUS: {status.upper()}")

            # Metadata Grid
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Vehicle Plate:** `:red[{record['plate_number']}]`")
                st.markdown(f"**Violation:** `{record['offense']}`")
                st.markdown(f"**Camera Terminal:** `{record['camera_id']}`")
            with c2:
                st.markdown(f"**Timestamp:** `{record['timestamp']}`")
                st.markdown(f"**Fine Penalty:** `₹{record['fine_amount']:,}`")
                st.markdown(f"**Location:** `{record['location']}`")

            st.divider()

            # Tripartite Evidence Display
            st.markdown("#### 📸 Tripartite Photographic Proof")
            ev_col1, ev_col2 = st.columns([5, 4])

            with ev_col1:
                full_img = record.get("full_image_path", "")
                if full_img and os.path.exists(full_img):
                    st.image(full_img, caption="1. Full Scene Traffic Context", use_container_width=True)
                else:
                    st.info("Full scene context image archived or in cloud storage.")

            with ev_col2:
                rider_img = record.get("rider_image_path", "")
                if rider_img and os.path.exists(rider_img):
                    st.image(rider_img, caption="2. Zoomed Rider Head [NO HELMET]", use_container_width=True)

                plate_img = record.get("plate_image_path", "")
                if plate_img and os.path.exists(plate_img):
                    st.image(plate_img, caption=f"3. Plate OCR ROI ({record['plate_number']})", use_container_width=True)

            st.divider()

            # Legal Dispatch and PDF Management
            st.markdown("#### ⚖️ Legal Dispatch & Digital Enforcement")

            # Check or generate PDF
            pdf_path = record.get("pdf_path", "")
            if not pdf_path or not os.path.exists(pdf_path):
                # Generate on the fly
                pdf_path = generate_challan_pdf(
                    challan_id=record["challan_id"],
                    track_id=record["track_id"],
                    timestamp=record["timestamp"],
                    plate_number=record["plate_number"],
                    confidence=record["confidence"],
                    location=record["location"],
                    camera_id=record["camera_id"],
                    fine_amount=record["fine_amount"],
                    full_image_path=record.get("full_image_path", ""),
                    rider_image_path=record.get("rider_image_path", ""),
                    plate_image_path=record.get("plate_image_path", "")
                )

            # PDF Download Button
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📄 Download Official A4 E-Challan PDF",
                        data=pdf_file.read(),
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )

            # Action Buttons
            act_col1, act_col2 = st.columns(2)
            with act_col1:
                if record["status"] != "Paid":
                    if st.button("✅ Mark as Paid", key=f"pay_{record['challan_id']}", use_container_width=True):
                        update_violation_status(record["challan_id"], "Paid", notes="Marked paid manually by officer")
                        st.success("Citation marked as Paid!")
                        st.rerun()
            with act_col2:
                if st.button("📲 Simulate SMS / WhatsApp Notice", key=f"sms_{record['challan_id']}", use_container_width=True):
                    st.toast(f"Digital citation sent to owner of {record['plate_number']} via NIC mParivahan Gateway!", icon="📨")
    else:
        st.info("Select any citation from the left list to view case details.")
