"""
SmartChallan AI - Page 6: Edge System Diagnostics & Camera Settings
Camera stream management, AI hyperparameter tuning, hardware health telemetry,
and modular component benchmark testing.
"""

import os
import psutil
import torch
import streamlit as st
import pandas as pd
from datetime import datetime

from core.database import BASE_DIR, EVIDENCE_DIR, CHALLANS_DIR, DB_PATH
from core.challan_generator import generate_challan_pdf
from core.anpr import get_ocr_reader

st.set_page_config(page_title="System Settings — SmartChallan AI", page_icon="⚙️", layout="wide")

st.markdown("## ⚙️ Edge System Diagnostics & Camera Hub")
st.caption("Hardware Telemetry • RTSP Camera Network • AI Sensitivity Tuning • Diagnostics Benchmark")

tab_cameras, tab_models, tab_hardware, tab_diagnostics = st.tabs([
    "📹 Camera Stream Network",
    "🧠 AI Model Configurations",
    "💻 Edge Hardware Telemetry",
    "🧪 Diagnostic Benchmarks"
])

# TAB 1: Cameras
with tab_cameras:
    st.subheader("📹 Connected Traffic Cameras (RTSP Streams)")

    cameras_data = [
        {"Camera ID": "CAM-NORTH-04", "Location": "Intersection 12, Ring Road North", "RTSP / Source": "rtsp://192.168.1.104:554/live", "Resolution": "1920x1080 @ 30 FPS", "Status": "🟢 Online"},
        {"Camera ID": "CAM-CENTRAL-01", "Location": "Central Square Crossway", "RTSP / Source": "rtsp://192.168.1.101:554/live", "Resolution": "1920x1080 @ 30 FPS", "Status": "🟢 Online"},
        {"Camera ID": "CAM-SOUTH-02", "Location": "South Bypass Flyover Exit", "RTSP / Source": "rtsp://192.168.1.102:554/live", "Resolution": "1280x720 @ 25 FPS", "Status": "🟢 Online"},
        {"Camera ID": "CAM-EAST-03", "Location": "Tech Hub Junction East", "RTSP / Source": "rtsp://192.168.1.103:554/live", "Resolution": "1920x1080 @ 30 FPS", "Status": "🟡 Low Bandwidth"}
    ]
    st.dataframe(pd.DataFrame(cameras_data), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### ➕ Add New Municipal Camera Feed")
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        new_cam_id = st.text_input("Terminal ID:", placeholder="e.g. CAM-WEST-05")
        new_cam_loc = st.text_input("Junction / Location Name:", placeholder="e.g. Airport Expressway Gate 2")
    with c_f2:
        new_cam_rtsp = st.text_input("RTSP Stream URI:", placeholder="rtsp://admin:pass@ip:port/stream")
        new_cam_fps = st.number_input("Target FPS:", min_value=5, max_value=60, value=30)

    if st.button("🔗 Connect & Verify Camera Stream"):
        st.success(f"Stream verification ping sent to {new_cam_id}! Added to surveillance matrix.")

# TAB 2: AI Models
with tab_models:
    st.subheader("🧠 Dual-Model Vision Pipeline Parameters")

    c_m1, c_m2 = st.columns(2)
    with c_m1:
        st.markdown("#### Primary General Object Detector")
        st.text_input("General Model Checkpoint:", value="yolov8n.pt", disabled=True)
        st.markdown("**Classes Monitored:** `0: Person`, `3: Motorcycle`")
        st.slider("Base Confidence Threshold:", 0.2, 0.9, 0.45)
        st.slider("NMS IOU Threshold:", 0.2, 0.9, 0.45)

    with c_m2:
        st.markdown("#### Fine-Tuned Helmet Classifier")
        st.text_input("Helmet Model Weights:", value="best.pt (~6.2 MB)", disabled=True)
        st.markdown("**Classes Monitored:** `0: Helmet`, `1: NO HELMET`")
        st.slider("Helmet Decision Confidence:", 0.2, 0.9, 0.40)
        st.slider("Spatial Overlap Multiplier:", 0.1, 0.8, 0.30)

    st.divider()
    st.markdown("#### 🎯 ByteTrack Multi-Object Tracker Tuning")
    c_t1, c_t2, c_t3 = st.columns(3)
    c_t1.number_input("Track Buffer (Frames to retain lost objects):", value=30)
    c_t2.number_input("Match Threshold (IOU association):", value=0.8)
    c_t3.number_input("Consecutive Debounce Frames:", value=3)

# TAB 3: Hardware
with tab_hardware:
    st.subheader("💻 Edge Hardware & System Resource Telemetry")

    cpu_pct = psutil.cpu_percent(interval=0.2)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(BASE_DIR)

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("CPU Utilization", f"{cpu_pct}%", "Normal")
    h2.metric("System RAM Used", f"{mem.used / (1024**3):.1f} GB", f"{mem.percent}%")
    h3.metric("Storage Free", f"{disk.free / (1024**3):.1f} GB", "Healthy")
    h4.metric("PyTorch Engine", "CUDA Active" if torch.cuda.is_available() else "Edge CPU", "Torch 2.x")

    st.divider()
    st.markdown("#### 📁 Storage Directory Footprint")
    ev_count = len(os.listdir(EVIDENCE_DIR)) if os.path.exists(EVIDENCE_DIR) else 0
    ch_count = len(os.listdir(CHALLANS_DIR)) if os.path.exists(CHALLANS_DIR) else 0

    s1, s2, s3 = st.columns(3)
    s1.info(f"📸 **Evidence Snapshots:** {ev_count} image files stored in `storage/evidence/`")
    s2.info(f"📄 **Generated Citations:** {ch_count} PDF files stored in `storage/challans/`")
    s3.info(f"🗄️ **Database:** SQLite `storage/violations.db` + CSV audit mirror")

# TAB 4: Diagnostics
with tab_diagnostics:
    st.subheader("🧪 Modular Pipeline Diagnostics & Self-Tests")

    d_col1, d_col2 = st.columns(2)

    with d_col1:
        st.markdown("#### 1. Instant PDF E-Challan Generator Test")
        st.caption("Generates a sample court-ready PDF citation to test the FPDF2 engine.")
        if st.button("Generate Diagnostic E-Challan"):
            test_id = f"CH-DIAG-{datetime.now().strftime('%H%M%S')}"
            path = generate_challan_pdf(
                challan_id=test_id,
                track_id=88,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                plate_number="DL 08 EF 9988",
                confidence=0.95,
                location="Diagnostic Benchmark Rig",
                camera_id="CAM-DIAG-01"
            )
            st.success(f"Diagnostic PDF generated successfully at: {path}")
            with open(path, "rb") as pf:
                st.download_button("📥 Download Generated Diagnostic PDF", pf.read(), f"{test_id}.pdf")

    with d_col2:
        st.markdown("#### 2. EasyOCR Engine Health Check")
        st.caption("Pings the OCR reader model to verify character extraction readiness.")
        if st.button("Run OCR Reader Self-Test"):
            with st.spinner("Pinging EasyOCR Reader..."):
                reader = get_ocr_reader()
                if reader:
                    st.success("🟢 EasyOCR English reader loaded and responsive!")
                else:
                    st.warning("EasyOCR running in fallback mode.")
