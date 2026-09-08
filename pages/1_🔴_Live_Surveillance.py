"""
SmartChallan AI - Page 1: Live Surveillance & Violation Detection
Real-time edge video processing, hierarchical rider-motorcycle coupling,
ByteTrack de-duplication, and instant digital E-Challan issuance.
"""

import os
import time
import tempfile
import cv2
import numpy as np
import streamlit as st
from PIL import Image

from core.detector import HierarchicalHelmetDetector
from core.tracker import VehicleViolationTracker
from core.database import get_all_violations

st.set_page_config(page_title="Live Surveillance — SmartChallan AI", page_icon="🔴", layout="wide")

st.markdown("## 🔴 Real-Time Surveillance & Violation Detection")
st.caption("Autonomous Edge Video Pipeline • Hierarchical Spatial Pairing • ByteTrack De-Duplication • Instant Citation")

# Setup default video path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_VIDEO = os.path.join(BASE_DIR, "Code_Execution.mp4")

# Sidebar Controls
with st.sidebar:
    st.markdown("### ⚙️ Video Feed Source")
    feed_mode = st.radio(
        "Select Stream Input:",
        ["Sample Traffic Feed (Code_Execution.mp4)", "Upload Custom Video File", "Live Web Camera (Index 0)"],
        index=0
    )

    video_path = DEFAULT_VIDEO

    if feed_mode == "Upload Custom Video File":
        uploaded = st.file_uploader("Upload MP4 / MOV Video", type=["mp4", "mov", "avi"])
        if uploaded:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tfile.write(uploaded.read())
            video_path = tfile.name
    elif feed_mode == "Live Web Camera (Index 0)":
        video_path = 0

    st.divider()
    st.markdown("### 🎛️ AI Sensitivity Tuning")
    conf_thresh = st.slider("YOLO Detection Confidence", 0.20, 0.85, 0.45, 0.05)
    overlap_thresh = st.slider("Rider-Motorcycle Overlap (IOU)", 0.15, 0.60, 0.30, 0.05)
    consec_frames = st.slider("Consecutive Violation Frames (Debounce)", 1, 6, 2, 1)

    st.divider()
    camera_id = st.text_input("Surveillance Camera ID", value="CAM-NORTH-04")
    location = st.text_input("Junction Location", value="Intersection 12, Ring Road North")

    st.divider()
    max_frames_to_run = st.number_input("Max Frames to Process (0 = Entire Feed)", min_value=0, max_value=3000, value=250, step=50)

# Layout: 2 Columns (Left: Video Player & Controls, Right: Real-Time Violation Ticker)
col_stream, col_ticker = st.columns([13, 7])

with col_stream:
    # Action Buttons
    c_btn1, c_btn2, c_btn3 = st.columns([2, 2, 3])
    with c_btn1:
        start_button = st.button("▶️ Start Live Stream", type="primary", use_container_width=True)
    with c_btn2:
        stop_button = st.button("⏹️ Stop Stream", use_container_width=True)
    with c_btn3:
        if st.button("🔄 Reset Tracking Cache", use_container_width=True):
            st.session_state["reset_cache"] = True
            st.success("Tracking cache cleared.")

    # Live Video Display placeholder
    video_placeholder = st.empty()

    # Real-time metrics strip
    m1, m2, m3, m4 = st.columns(4)
    metric_fps = m1.empty()
    metric_vehicles = m2.empty()
    metric_violations = m3.empty()
    metric_pedestrians = m4.empty()

    # Initial metric display
    metric_fps.metric("Processing FPS", "0.0")
    metric_vehicles.metric("Active Motorcycles", "0")
    metric_violations.metric("Violations Confirmed", "0")
    metric_pedestrians.metric("Pedestrians Filtered", "0")

with col_ticker:
    st.markdown("### 🚨 Live Violation Feed")
    st.caption("New violations stream live below with automatic PDF E-Challans.")
    ticker_placeholder = st.empty()


def render_violation_cards(violations_list):
    """Renders sleek HTML cards for recent violations in the right column."""
    if not violations_list:
        ticker_placeholder.info("Monitoring stream... No violations detected yet.")
        return

    with ticker_placeholder.container():
        for v in violations_list[:5]:
            with st.container(border=True):
                c_head1, c_head2 = st.columns([3, 2])
                with c_head1:
                    st.markdown(f"**Challan:** `{v['challan_id']}`")
                    st.markdown(f"**Plate:** `:red[{v['plate_number']}]`")
                with c_head2:
                    st.caption(f"Track #{v['track_id']}")
                    st.markdown("🔴 **NO HELMET**")

                # Show cropped images side by side if available
                img_col1, img_col2 = st.columns(2)
                with img_col1:
                    if os.path.exists(v.get("rider_img_path", "")):
                        st.image(v["rider_img_path"], caption="Rider Head", use_container_width=True)
                with img_col2:
                    if os.path.exists(v.get("plate_img_path", "")):
                        st.image(v["plate_img_path"], caption="License Plate", use_container_width=True)

                st.caption(f"📍 {v.get('location', 'Intersection 12')}")

                # Download PDF button
                pdf_path = v.get("pdf_path", "")
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Download E-Challan PDF",
                            data=f.read(),
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                            key=f"dl_{v['challan_id']}_{time.time()}",
                            use_container_width=True
                        )


# Render existing recent violations initially
initial_viols = get_all_violations(limit=4)
formatted_initial = []
for iv in initial_viols:
    formatted_initial.append({
        "challan_id": iv["challan_id"],
        "track_id": iv["track_id"],
        "plate_number": iv["plate_number"],
        "location": iv["location"],
        "rider_img_path": iv["rider_image_path"],
        "plate_img_path": iv["plate_image_path"],
        "pdf_path": iv["pdf_path"]
    })
render_violation_cards(formatted_initial)


# Video Streaming Logic
if start_button:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        st.error(f"Cannot open video source: {video_path}")
    else:
        # Load detector and tracker
        detector = HierarchicalHelmetDetector(conf_thresh=conf_thresh, overlap_thresh=overlap_thresh)
        tracker = VehicleViolationTracker(
            consecutive_frames_thresh=consec_frames,
            camera_id=camera_id,
            location=location
        )

        frame_count = 0
        t0 = time.time()
        live_violations = formatted_initial.copy()

        progress_bar = st.progress(0)
        total_stream_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_stream_frames <= 0:
            total_stream_frames = 300

        status_text = st.empty()
        status_text.success("🟢 Camera feed connected. Autonomous detection running...")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if max_frames_to_run > 0 and frame_count > max_frames_to_run:
                break

            # Process frame
            h_res = detector.detect_and_associate(frame)
            annotated_frame, new_viols = tracker.process_frame(frame, h_res, frame_idx=frame_count)

            # Update violations feed if any new
            if new_viols:
                for nv in new_viols:
                    live_violations.insert(0, nv)
                render_violation_cards(live_violations)

            # Calculate FPS
            elapsed = time.time() - t0
            cur_fps = frame_count / max(elapsed, 0.001)

            # Convert BGR frame to RGB for Streamlit
            rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            video_placeholder.image(rgb_frame, channels="RGB", use_container_width=True)

            # Update metrics
            metric_fps.metric("Processing FPS", f"{cur_fps:.1f}")
            metric_vehicles.metric("Active Motorcycles", str(len(tracker.total_tracked_vehicles)))
            metric_violations.metric("Violations Confirmed", str(len(tracker.processed_track_ids)))
            metric_pedestrians.metric("Pedestrians Filtered", str(h_res.get("pedestrians_ignored", 0)))

            # Update progress bar
            pct = min(frame_count / float(max_frames_to_run if max_frames_to_run > 0 else total_stream_frames), 1.0)
            progress_bar.progress(pct)

        cap.release()
        status_text.info(f"Stream finished. Processed {frame_count} frames at average {cur_fps:.1f} FPS.")
