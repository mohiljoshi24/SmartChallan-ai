"""
SmartChallan AI - Frontend Mock Data Provider
Provides rich, realistic demonstration data for independent frontend UI testing
before connecting live backend pipelines.
"""

from datetime import datetime, timedelta

MOCK_KPIS = {
    "total_vehicles": 148,
    "total_violations": 14,
    "compliance_rate": 90.5,
    "total_fine_amount": 14000,
    "recovered_fine": 8000,
    "active_cameras": 4,
    "avg_fps": 28.4
}

MOCK_CAMERAS = [
    {
        "id": "CAM-NORTH-04",
        "name": "Intersection 12 (Ring Road North)",
        "status": "Active",
        "fps": 30,
        "violations_today": 6
    },
    {
        "id": "CAM-CENTRAL-01",
        "name": "Central Square Crossway",
        "status": "Active",
        "fps": 30,
        "violations_today": 4
    },
    {
        "id": "CAM-SOUTH-02",
        "name": "South Bypass Flyover Exit",
        "status": "Active",
        "fps": 25,
        "violations_today": 3
    },
    {
        "id": "CAM-EAST-03",
        "name": "Tech Hub Junction East",
        "status": "Standby",
        "fps": 30,
        "violations_today": 1
    }
]

MOCK_VIOLATIONS = [
    {
        "challan_id": "CH-20260908-1001",
        "track_id": 4,
        "timestamp": (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
        "plate_number": "MH 12 AB 4592",
        "confidence": 0.94,
        "location": "Intersection 12, Ring Road North",
        "camera_id": "CAM-NORTH-04",
        "offense": "Section 129 / 194D MV Act - Riding Without Helmet",
        "fine_amount": 1000,
        "status": "Issued",
        "notes": "Automated ByteTrack verified detection."
    },
    {
        "challan_id": "CH-20260908-1002",
        "track_id": 9,
        "timestamp": (datetime.now() - timedelta(minutes=28)).strftime("%Y-%m-%d %H:%M:%S"),
        "plate_number": "KA 03 HA 8812",
        "confidence": 0.89,
        "location": "Central Square Crossway",
        "camera_id": "CAM-CENTRAL-01",
        "offense": "Section 129 / 194D MV Act - Riding Without Helmet",
        "fine_amount": 1000,
        "status": "Paid",
        "notes": "Paid via Citizen UPI Portal."
    },
    {
        "challan_id": "CH-20260908-1003",
        "track_id": 14,
        "timestamp": (datetime.now() - timedelta(minutes=39)).strftime("%Y-%m-%d %H:%M:%S"),
        "plate_number": "IND-TMP-14",
        "confidence": 0.61,
        "location": "South Bypass Flyover Exit",
        "camera_id": "CAM-SOUTH-02",
        "offense": "Section 129 / 194D MV Act - Riding Without Helmet",
        "fine_amount": 1000,
        "status": "Pending Review",
        "notes": "Partial mud occlusion on plate - operator review requested."
    },
    {
        "challan_id": "CH-20260908-1004",
        "track_id": 22,
        "timestamp": (datetime.now() - timedelta(minutes=52)).strftime("%Y-%m-%d %H:%M:%S"),
        "plate_number": "DL 01 CD 7731",
        "confidence": 0.92,
        "location": "Intersection 12, Ring Road North",
        "camera_id": "CAM-NORTH-04",
        "offense": "Section 129 / 194D MV Act - Riding Without Helmet",
        "fine_amount": 1000,
        "status": "Issued",
        "notes": "Digital citation SMS queued."
    },
    {
        "challan_id": "CH-20260908-1005",
        "track_id": 29,
        "timestamp": (datetime.now() - timedelta(minutes=74)).strftime("%Y-%m-%d %H:%M:%S"),
        "plate_number": "GJ 06 KL 9024",
        "confidence": 0.95,
        "location": "Tech Hub Junction East",
        "camera_id": "CAM-EAST-03",
        "offense": "Section 129 / 194D MV Act - Riding Without Helmet",
        "fine_amount": 1000,
        "status": "Contested",
        "notes": "Citizen requested photographic re-audit."
    },
    {
        "challan_id": "CH-20260908-1006",
        "track_id": 35,
        "timestamp": (datetime.now() - timedelta(minutes=90)).strftime("%Y-%m-%d %H:%M:%S"),
        "plate_number": "HR 26 DQ 5521",
        "confidence": 0.91,
        "location": "Intersection 12, Ring Road North",
        "camera_id": "CAM-NORTH-04",
        "offense": "Section 129 / 194D MV Act - Riding Without Helmet",
        "fine_amount": 1000,
        "status": "Paid",
        "notes": "Settled at municipal kiosk."
    }
]

HOURLY_TRAFFIC = [
    {"hour": "07:00", "vehicles": 25, "violations": 2},
    {"hour": "08:00", "vehicles": 65, "violations": 8},
    {"hour": "09:00", "vehicles": 140, "violations": 22},
    {"hour": "10:00", "vehicles": 110, "violations": 14},
    {"hour": "11:00", "vehicles": 75, "violations": 6},
    {"hour": "12:00", "vehicles": 50, "violations": 4},
    {"hour": "13:00", "vehicles": 45, "violations": 3},
    {"hour": "14:00", "vehicles": 55, "violations": 5},
    {"hour": "15:00", "vehicles": 70, "violations": 7},
    {"hour": "16:00", "vehicles": 95, "violations": 11},
    {"hour": "17:00", "vehicles": 135, "violations": 19},
    {"hour": "18:00", "vehicles": 160, "violations": 26},
    {"hour": "19:00", "vehicles": 120, "violations": 15},
    {"hour": "20:00", "vehicles": 80, "violations": 9}
]
