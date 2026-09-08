"""
SmartChallan AI - Page 5: Citizen Self-Service & E-Challan Payment Portal
Public-facing transparency portal allowing motorcyclists to look up challans by vehicle number,
view irrefutable photographic evidence, pay fines via UPI, or file grievances.
"""

import os
import time
import streamlit as st
import pandas as pd
from datetime import datetime

from core.database import (
    get_violations_by_plate,
    get_all_violations,
    update_violation_status
)

st.set_page_config(page_title="Citizen Portal — SmartChallan AI", page_icon="💳", layout="wide")

st.markdown("## 💳 Municipal Citizen E-Challan & Payment Portal")
st.caption("Official Citizen Services • Search Traffic Citations • View Photo Proof • Instant UPI Fine Settlement")

# Hero Search Section
st.markdown("""
<div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 1.5rem; border-radius: 12px; color: white; margin-bottom: 1.5rem;">
    <h3 style="margin-top:0; color:white;">🔍 Check Pending E-Challans for Your Vehicle</h3>
    <p style="margin-bottom:0.5rem; opacity: 0.9;">Enter your vehicle registration number to review photographic evidence and settle outstanding road-safety penalties.</p>
</div>
""", unsafe_allow_html=True)

# Search Input
c_search, c_demo = st.columns([3, 2])
with c_search:
    search_plate = st.text_input("Enter Vehicle Registration Number:", placeholder="e.g. MH 12 AB 4592").strip()

with c_demo:
    st.markdown("**Quick Demo Plates (Click to Test):**")
    demo_p1, demo_p2, demo_p3 = st.columns(3)
    with demo_p1:
        if st.button("MH 12 AB 4592"):
            search_plate = "MH 12 AB 4592"
    with demo_p2:
        if st.button("DL 01 CD 7731"):
            search_plate = "DL 01 CD 7731"
    with demo_p3:
        if st.button("KA 03 HA 8812"):
            search_plate = "KA 03 HA 8812"

st.write("")

if search_plate:
    records = get_violations_by_plate(search_plate)

    if not records:
        st.success(f"🎉 No outstanding helmet violations or pending challans found for vehicle **{search_plate.upper()}**! Thank you for wearing safety headgear.")
    else:
        st.warning(f"⚠️ Found **{len(records)}** citation record(s) for vehicle **{search_plate.upper()}**.")

        for rec in records:
            with st.container(border=True):
                # Header & Status
                h_col1, h_col2 = st.columns([3, 1])
                with h_col1:
                    st.markdown(f"### Citation Reference: `{rec['challan_id']}`")
                    st.markdown(f"**Offense:** `{rec['offense']}`")
                with h_col2:
                    if rec["status"] == "Paid":
                        st.success("🟢 PAID & CLEARED")
                    else:
                        st.error(f"🔴 UNPAID (₹{rec['fine_amount']:,})")

                # Details Grid
                d1, d2, d3 = st.columns(3)
                d1.markdown(f"**Location:** {rec['location']}")
                d2.markdown(f"**Camera Terminal:** {rec['camera_id']}")
                d3.markdown(f"**Incident Time:** {rec['timestamp']}")

                st.divider()

                # Photographic Evidence Viewer
                st.markdown("#### 📸 Official Photographic Evidence of Infraction")
                st.caption("Images captured by municipal edge-vision cameras at time of detection.")

                img_col1, img_col2, img_col3 = st.columns([5, 3, 3])
                with img_col1:
                    if rec.get("full_image_path") and os.path.exists(rec["full_image_path"]):
                        st.image(rec["full_image_path"], caption="Full Scene Context", use_container_width=True)
                    else:
                        st.info("Full scene context archived in police registry.")
                with img_col2:
                    if rec.get("rider_image_path") and os.path.exists(rec["rider_image_path"]):
                        st.image(rec["rider_image_path"], caption="Rider Head [NO HELMET]", use_container_width=True)
                with img_col3:
                    if rec.get("plate_image_path") and os.path.exists(rec["plate_image_path"]):
                        st.image(rec["plate_image_path"], caption="License Plate Sensor ROI", use_container_width=True)

                st.divider()

                # Payment or Clearance Section
                if rec["status"] != "Paid":
                    tab_pay, tab_dispute = st.tabs(["💳 Pay Fine Online (Instant Settlement)", "⚖️ File Citizen Dispute / Grievance"])

                    with tab_pay:
                        pay_c1, pay_c2 = st.columns([3, 2])
                        with pay_c1:
                            st.markdown(f"**Outstanding Penalty Amount:** `₹{rec['fine_amount']:,}`")
                            payment_method = st.radio("Select Payment Method:", ["UPI / QR Code", "Debit / Credit Card", "Net Banking"], horizontal=True)

                            if st.button(f"Proceed to Pay ₹{rec['fine_amount']:,} via {payment_method}", type="primary", key=f"user_pay_{rec['challan_id']}"):
                                with st.spinner("Processing secure transaction via Smart City Gateway..."):
                                    time.sleep(1.2)
                                    update_violation_status(rec["challan_id"], "Paid", notes="Settled online by citizen via UPI Gateway")
                                    st.success(f"Payment of ₹{rec['fine_amount']:,} Successful! Challan #{rec['challan_id']} is officially cleared.")
                                    st.toast("Transaction Reference: TXN-" + str(int(time.time())), icon="✅")
                                    st.rerun()

                        with pay_c2:
                            st.markdown("**Instant QR Settlement:**")
                            st.caption("Scan with Google Pay, PhonePe, or Paytm")
                            # Quick QR placeholder
                            st.code(f"upi://pay?pa=smartchallan@police&pn=TrafficDept&am={rec['fine_amount']}&tr={rec['challan_id']}", language="text")

                    with tab_dispute:
                        st.markdown("**Contest this Citation:**")
                        dispute_reason = st.selectbox("Reason for Dispute:", [
                            "I was wearing a certified helmet (Color / lighting issue)",
                            "Vehicle license plate was misread / incorrect vehicle",
                            "Vehicle was stolen / sold prior to incident",
                            "Emergency situation / medical exemption"
                        ], key=f"disp_r_{rec['challan_id']}")
                        dispute_details = st.text_area("Additional Explanatory Details:", key=f"disp_d_{rec['challan_id']}")

                        if st.button("Submit Contest for Police Review", key=f"disp_btn_{rec['challan_id']}"):
                            update_violation_status(rec["challan_id"], "Contested", notes=f"Citizen Grievance: {dispute_reason} - {dispute_details}")
                            st.info("Dispute submitted successfully. Citation routed to ANPR Review Desk for officer audit.")
                            st.rerun()

                else:
                    st.success(f"Citation #{rec['challan_id']} is cleared! Transaction ID: TXN-20260908-{rec['track_id']}")
                    if rec.get("pdf_path") and os.path.exists(rec["pdf_path"]):
                        with open(rec["pdf_path"], "rb") as pf:
                            st.download_button("📥 Download Clearance Certificate / Receipt", pf.read(), f"Receipt_{rec['challan_id']}.pdf", "application/pdf")
else:
    st.info("💡 Enter your vehicle plate number above or click any demo plate to inspect.")
