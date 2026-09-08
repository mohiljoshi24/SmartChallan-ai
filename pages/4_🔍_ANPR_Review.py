"""
SmartChallan AI - Page 4: ANPR Review & Officer Verification Hub
Human-in-the-loop quality control interface for reviewing low-confidence plate readings,
provisional IDs, and officer adjudication before legal notice dispatch.
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime

from core.database import (
    get_all_violations,
    get_violation_by_id,
    update_violation_status
)
from core.challan_generator import generate_challan_pdf

st.set_page_config(page_title="ANPR Review — SmartChallan AI", page_icon="🔍", layout="wide")

st.markdown("## 🔍 ANPR Review & Officer Verification Hub")
st.caption("Human-in-the-Loop Quality Assurance • License Plate Adjudication • False Positive Dismissal")

# Load violations needing verification
all_viols = get_all_violations(limit=100)
pending_queue = [
    v for v in all_viols
    if v["status"] == "Pending Review" or "TMP" in v["plate_number"]
]

col_queue, col_verify = st.columns([5, 7])

with col_queue:
    st.subheader(f"📥 Verification Queue ({len(pending_queue)} Pending)")

    if not pending_queue:
        st.success("🎉 All captured violations have verified license plates! No items pending.")
        selected_challan = None
    else:
        options = [f"{v['challan_id']} | Current: {v['plate_number']} (Conf: {int(v['confidence']*100)}%)" for v in pending_queue]
        chosen = st.radio("Select Case to Adjudicate:", options, label_visibility="collapsed")
        selected_challan = chosen.split(" | ")[0]

with col_verify:
    st.subheader("🛠️ Officer Verification Station")

    if selected_challan:
        record = get_violation_by_id(selected_challan)
        if record:
            st.markdown(f"### Reviewing Case #{record['challan_id']}")
            st.caption(f"Captured at {record['location']} • Camera {record['camera_id']}")

            # Images: Rider Head and License Plate
            c_img1, c_img2 = st.columns(2)
            with c_img1:
                if record.get("rider_image_path") and os.path.exists(record["rider_image_path"]):
                    st.image(record["rider_image_path"], caption="Rider Head Crop [Violation Proof]", use_container_width=True)
                else:
                    st.info("Rider crop archived.")

            with c_img2:
                if record.get("plate_image_path") and os.path.exists(record["plate_image_path"]):
                    st.image(record["plate_image_path"], caption="Plate Crop (Camera Sensor)", use_container_width=True)
                else:
                    st.info("Plate crop archived.")

            st.divider()

            # Plate Correction Form
            st.markdown("#### ✍️ Plate Verification & Corrections")
            current_plate = record["plate_number"]

            c_edit1, c_edit2 = st.columns([3, 2])
            with c_edit1:
                corrected_plate = st.text_input(
                    "Verified Registration Number:",
                    value=current_plate,
                    help="Enter standard alphanumeric vehicle plate e.g. MH 12 AB 1234"
                )
            with c_edit2:
                st.metric("AI OCR Confidence", f"{int(record['confidence']*100)}%", "Low Quality Flagged" if "TMP" in current_plate else "Acceptable")

            officer_notes = st.text_area("Officer Audit Notes:", value=f"Verified by Traffic Desk Officer on {datetime.now().strftime('%d-%b %H:%M')}")

            col_action1, col_action2 = st.columns(2)

            with col_action1:
                if st.button("✅ Confirm Plate & Seal Official Challan", type="primary", use_container_width=True):
                    # Regenerate PDF with verified plate
                    pdf_path = generate_challan_pdf(
                        challan_id=record["challan_id"],
                        track_id=record["track_id"],
                        timestamp=record["timestamp"],
                        plate_number=corrected_plate.upper(),
                        confidence=0.99,  # Human verified
                        location=record["location"],
                        camera_id=record["camera_id"],
                        fine_amount=record["fine_amount"],
                        full_image_path=record.get("full_image_path", ""),
                        rider_image_path=record.get("rider_image_path", ""),
                        plate_image_path=record.get("plate_image_path", "")
                    )

                    update_violation_status(
                        challan_id=record["challan_id"],
                        new_status="Issued",
                        notes=officer_notes,
                        new_plate=corrected_plate.upper()
                    )

                    st.success(f"Challan #{record['challan_id']} sealed with verified plate {corrected_plate.upper()}!")
                    st.rerun()

            with col_action2:
                if st.button("❌ Dismiss Violation (False Positive)", use_container_width=True):
                    update_violation_status(
                        challan_id=record["challan_id"],
                        new_status="Dismissed",
                        notes=f"Dismissed by Officer: {officer_notes}"
                    )
                    st.warning(f"Violation #{record['challan_id']} dismissed and voided.")
                    st.rerun()

    else:
        st.info("Select any item in the verification queue on the left to begin review.")
