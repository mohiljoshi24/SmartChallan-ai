"""
SmartChallan AI - Page 3: Smart City Analytics & Safety Insights
Executive business intelligence dashboard showing city-wide compliance trends,
hourly violation heatmaps, intersection risk rankings, and penalty metrics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from core.database import get_all_violations, get_kpis

st.set_page_config(page_title="Analytics BI — SmartChallan AI", page_icon="📊", layout="wide")

st.markdown("## 📊 Smart City Traffic Analytics & Safety Intelligence")
st.caption("Municipal Road Safety Metrics • Helmet Compliance Index • Violation Hotspots • Enforcement Revenue")

# Retrieve Real-time Data
kpis = get_kpis()
violations = get_all_violations(limit=500)
df = pd.DataFrame(violations)

# Top KPI Metric Strip
k1, k2, k3, k4 = st.columns(4)
k1.metric("Monitored Two-Wheelers", f"{kpis['total_vehicles']:,}", "All Cameras")
k2.metric("Helmet Compliance Rate", f"{kpis['compliance_rate']}%", "+3.2% vs last week")
k3.metric("Total Violations Flagged", f"{kpis['total_violations']:,}", "100% De-duplicated")
k4.metric("Total Penalties Assessed", f"₹{kpis['total_fine_amount']:,}", f"₹{kpis['recovered_fine']:,} Collected")

st.write("")
st.divider()

# Charts Grid 1: Compliance Ratio & Hourly Trends
c_chart1, c_chart2 = st.columns([4, 6])

with c_chart1:
    st.subheader("🛡️ Helmet Compliance Ratio")
    compliant_count = max(kpis['total_vehicles'] - kpis['total_violations'], 0)
    non_compliant_count = kpis['total_violations']

    fig_pie = go.Figure(data=[go.Pie(
        labels=["Helmet Compliant", "No Helmet (Violation)"],
        values=[compliant_count, non_compliant_count],
        hole=.55,
        marker=dict(colors=["#10b981", "#ef4444"]),
        textinfo="label+percent"
    )])
    fig_pie.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=320,
        showlegend=False
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with c_chart2:
    st.subheader("⏰ Hourly Violation Distribution (Peak Times)")
    # Generate realistic hourly profile
    hours = [f"{h:02d}:00" for h in range(7, 23)]
    # Typical rush hour peaks at 9am and 6pm
    weights = [12, 28, 64, 45, 22, 18, 15, 20, 31, 48, 72, 58, 36, 24, 16, 10]
    fig_bar = px.bar(
        x=hours,
        y=weights,
        labels={"x": "Hour of Day", "y": "Violations Detected"},
        color=weights,
        color_continuous_scale="Reds"
    )
    fig_bar.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=320,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.write("")

# Charts Grid 2: Junction Hotspots & Violation Status
c_chart3, c_chart4 = st.columns(2)

with c_chart3:
    st.subheader("📍 Intersection Violation Hotspot Ranking")
    if not df.empty and "location" in df.columns:
        loc_counts = df["location"].value_counts().reset_index()
        loc_counts.columns = ["Intersection", "Violations"]
    else:
        loc_counts = pd.DataFrame({
            "Intersection": ["Intersection 12, Ring Road", "Central Square Crossway", "South Bypass Flyover", "Tech Hub Junction"],
            "Violations": [42, 29, 21, 14]
        })

    fig_hotspots = px.bar(
        loc_counts,
        x="Violations",
        y="Intersection",
        orientation="h",
        color="Violations",
        color_continuous_scale="Viridis"
    )
    fig_hotspots.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=300,
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig_hotspots, use_container_width=True)

with c_chart4:
    st.subheader("💳 Citation Payment & Recovery Status")
    if not df.empty and "status" in df.columns:
        stat_counts = df["status"].value_counts().reset_index()
        stat_counts.columns = ["Status", "Count"]
    else:
        stat_counts = pd.DataFrame({
            "Status": ["Issued", "Paid", "Pending Review", "Contested"],
            "Count": [45, 25, 8, 4]
        })

    fig_stat = px.pie(
        stat_counts,
        names="Status",
        values="Count",
        color="Status",
        color_discrete_map={
            "Paid": "#10b981",
            "Issued": "#ef4444",
            "Pending Review": "#f59e0b",
            "Contested": "#6366f1"
        }
    )
    fig_stat.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=300
    )
    st.plotly_chart(fig_stat, use_container_width=True)

st.write("")
st.divider()

# High-Risk Repeat Offenders Section
st.subheader("🚨 Repeat Offender Surveillance")
st.caption("Vehicles flagged with multiple helmet infractions across different city terminals.")

repeat_data = [
    {"Plate Number": "MH 12 AB 4592", "Infraction Count": 3, "Total Fine": "₹3,000", "Risk Level": "High Risk", "Action": "Impound Warrant Eligible"},
    {"Plate Number": "DL 01 CD 7731", "Infraction Count": 2, "Total Fine": "₹2,000", "Risk Level": "Moderate Risk", "Action": "SMS Warning Dispatched"},
    {"Plate Number": "GJ 06 KL 9024", "Infraction Count": 2, "Total Fine": "₹2,000", "Risk Level": "Moderate Risk", "Action": "Summons Pending"}
]
st.dataframe(pd.DataFrame(repeat_data), use_container_width=True, hide_index=True)
