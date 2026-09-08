"""
SmartChallan AI - Smart City Command Center (Main Hub)
Autonomous Vision-Based Helmet Violation Detection & Instant E-Challan Issuance System
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime

from core.database import init_db, seed_sample_data_if_empty, get_kpis, get_all_violations

# Page Configuration
st.set_page_config(
    page_title="SmartChallan AI — Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Tech Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4b5563;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 0.3rem;
    }
    .kpi-subtext {
        font-size: 0.8rem;
        color: #10b981;
        margin-top: 0.2rem;
    }
    .badge-fined {
        background-color: #fee2e2;
        color: #991b1b;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
    }
    .badge-paid {
        background-color: #d1fae5;
        color: #065f46;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
    }
    .badge-review {
        background-color: #fef3c7;
        color: #92400e;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database & seed demo records
init_db()
seed_sample_data_if_empty()

# Sidebar Brand & System Status
with st.sidebar:
    st.markdown("### 🛡️ SmartChallan AI")
    st.markdown("**Autonomous Road Safety Enforcement**")
    st.caption("Intelligent Transportation Systems (ITS) | Edge Vision")
    st.divider()

    st.markdown("#### ⚡ System Operational Status")
    st.success("🟢 Edge Inference Engine: ACTIVE")
    st.info("📹 Active Cameras: 4 Connected")
    st.info("🧠 Dual Model: YOLOv8n + best.pt")
    st.info("🎯 Tracker: ByteTrack v2.0")
    st.divider()

    st.markdown("#### 📂 Quick Navigation")
    st.markdown("""
    - [🔴 Live Surveillance](/Live_Surveillance)
    - [📑 Challan Registry](/Challan_Registry)
    - [📊 Analytics Dashboard](/Analytics_Dashboard)
    - [🔍 ANPR Review Desk](/ANPR_Review)
    - [💳 Citizen Portal](/Citizen_Portal)
    - [⚙️ System Settings](/System_Settings)
    """)
    st.divider()
    st.caption("SmartChallan AI v1.0.0 • Municipal Traffic Police")

# Main Header Banner
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<div class="main-header">🛡️ SmartChallan AI Command Center</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Autonomous Vision-Based Helmet Violation Detection & Instant E-Challan Issuance System</div>', unsafe_allow_html=True)
with col_h2:
    st.markdown(f"**Current Session Time:**  \n`{datetime.now().strftime('%d %b %Y | %H:%M:%S')}`")

# Fetch Real-Time KPIs
kpis = get_kpis()

# Top KPI Metric Strip
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Vehicles Monitored</div>
        <div class="kpi-value">{kpis['total_vehicles']}</div>
        <div class="kpi-subtext">Across 4 Intersection Feeds</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Violations Flagged</div>
        <div class="kpi-value" style="color: #dc2626;">{kpis['total_violations']}</div>
        <div class="kpi-subtext" style="color: #dc2626;">100% De-duplicated (ByteTrack)</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Helmet Compliance Rate</div>
        <div class="kpi-value" style="color: #2563eb;">{kpis['compliance_rate']}%</div>
        <div class="kpi-subtext">Target Threshold: 90.0%</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Penalty Assessed</div>
        <div class="kpi-value" style="color: #059669;">₹{kpis['total_fine_amount']:,}</div>
        <div class="kpi-subtext">Recovered: ₹{kpis['recovered_fine']:,} ({int(kpis['recovered_fine']/max(kpis['total_fine_amount'], 1)*100)}%)</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

# Operational Workflow & Module Launchpads
st.subheader("🚀 Operational Command Modules")
m1, m2, m3 = st.columns(3)

with m1:
    with st.container(border=True):
        st.markdown("### 🔴 Live Surveillance Feed")
        st.markdown("Real-time video inference on traffic streams. Couples riders to motorcycles, performs ByteTrack ID tracking, and auto-generates citations.")
        st.page_link("pages/1_🔴_Live_Surveillance.py", label="Open Live Surveillance →", icon="📹")

with m2:
    with st.container(border=True):
        st.markdown("### 📑 E-Challan Registry")
        st.markdown("Central court-admissible audit vault. View, filter, and inspect tripartite photo evidence (Full Frame, Rider Head, Plate) and download signed PDFs.")
        st.page_link("pages/2_📑_Challan_Registry.py", label="Open Challan Registry →", icon="📄")

with m3:
    with st.container(border=True):
        st.markdown("### 📊 Safety Analytics BI")
        st.markdown("Executive business intelligence for traffic commissioners: hourly violation distributions, compliance trends, junction hotspots, and fine revenue.")
        st.page_link("pages/3_📊_Analytics_Dashboard.py", label="Open Analytics BI →", icon="📈")

m4, m5, m6 = st.columns(3)

with m4:
    with st.container(border=True):
        st.markdown("### 🔍 ANPR Review Desk")
        st.markdown("Human-in-the-loop verification desk. Quality assurance officers inspect low-confidence plate readings and provisional tickets before final dispatch.")
        st.page_link("pages/4_🔍_ANPR_Review.py", label="Open ANPR Review Desk →", icon="🔎")

with m5:
    with st.container(border=True):
        st.markdown("### 💳 Citizen Self-Service Portal")
        st.markdown("Public transparency interface. Motorcyclists can search their vehicle registration number, inspect photo proof of offense, and pay online via UPI.")
        st.page_link("pages/5_💳_Citizen_Portal.py", label="Open Citizen Portal →", icon="💳")

with m6:
    with st.container(border=True):
        st.markdown("### ⚙️ System & Camera Settings")
        st.markdown("Configure multi-camera RTSP inputs, adjust YOLO confidence thresholds, tweak ByteTrack buffer frames, and monitor edge hardware performance.")
        st.page_link("pages/6_⚙️_System_Settings.py", label="Open System Settings →", icon="⚙️")

st.write("")
st.divider()

# Recent Real-Time Violations Table
st.subheader("⚡ Live Incident Audit Log (Recent Violations)")
recent_violations = get_all_violations(limit=6)

if recent_violations:
    table_data = []
    for v in recent_violations:
        table_data.append({
            "Challan ID": v["challan_id"],
            "Timestamp": v["timestamp"],
            "Vehicle Plate": v["plate_number"],
            "Camera Location": v["location"],
            "Fine (INR)": f"₹{v['fine_amount']:,}",
            "Status": v["status"],
            "Officer / AI Notes": v["officer_notes"]
        })
    df_recent = pd.DataFrame(table_data)
    st.dataframe(df_recent, use_container_width=True, hide_index=True)
else:
    st.info("No violations recorded yet in this session.")
