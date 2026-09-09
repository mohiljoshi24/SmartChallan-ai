"""
SmartChallan AI - Database & Persistence Layer
Handles SQLite storage, CSV audit export, violation querying, and demo seeding.
"""

import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
DB_PATH = os.path.join(STORAGE_DIR, "violations.db")
CSV_PATH = os.path.join(STORAGE_DIR, "violations.csv")
EVIDENCE_DIR = os.path.join(STORAGE_DIR, "evidence")
CHALLANS_DIR = os.path.join(STORAGE_DIR, "challans")

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs(CHALLANS_DIR, exist_ok=True)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema and exports initial CSV mirror."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challan_id TEXT UNIQUE NOT NULL,
            track_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            plate_number TEXT NOT NULL,
            confidence REAL NOT NULL,
            location TEXT NOT NULL,
            camera_id TEXT NOT NULL,
            offense TEXT NOT NULL,
            fine_amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Issued',
            full_image_path TEXT,
            rider_image_path TEXT,
            plate_image_path TEXT,
            pdf_path TEXT,
            officer_notes TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()
    sync_to_csv()


def sync_to_csv():
    """Syncs the SQLite violations table into storage/violations.csv for audit logs."""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM violations ORDER BY id DESC", conn)
        conn.close()
        df.to_csv(CSV_PATH, index=False)
    except Exception as e:
        print(f"[SmartChallan DB] Warning syncing to CSV: {e}")


def insert_violation(
    challan_id: str,
    track_id: int,
    timestamp: str,
    plate_number: str,
    confidence: float,
    location: str,
    camera_id: str,
    offense: str = "Section 129 / 194D MV Act - Helmet Non-Compliance",
    fine_amount: int = 1000,
    status: str = "Issued",
    full_image_path: str = "",
    rider_image_path: str = "",
    plate_image_path: str = "",
    pdf_path: str = "",
    officer_notes: str = ""
) -> Optional[int]:
    """Inserts a new violation record and updates the CSV."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO violations (
                challan_id, track_id, timestamp, plate_number, confidence,
                location, camera_id, offense, fine_amount, status,
                full_image_path, rider_image_path, plate_image_path, pdf_path, officer_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            challan_id, int(track_id), timestamp, plate_number, round(confidence, 2),
            location, camera_id, offense, fine_amount, status,
            full_image_path, rider_image_path, plate_image_path, pdf_path, officer_notes
        ))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        sync_to_csv()
        return last_id
    except sqlite3.IntegrityError:
        conn.close()
        return None
    except Exception as e:
        conn.close()
        print(f"[SmartChallan DB] Error inserting violation: {e}")
        return None


def format_row_for_web(row: Any) -> Dict[str, Any]:
    """Sanitizes row data, converting numpy/bytes track_ids and normalizing image paths for web frontend."""
    d = dict(row)
    # Ensure track_id is standard int, not bytes or numpy type
    tid = d.get("track_id")
    if isinstance(tid, (bytes, bytearray)):
        d["track_id"] = int.from_bytes(tid, 'little') if len(tid) <= 8 else 1
    else:
        try:
            d["track_id"] = int(tid) if tid is not None else 1
        except Exception:
            d["track_id"] = 1

    # Normalize image and PDF paths to relative web URLs (e.g. storage/evidence/filename.jpg)
    for img_key, placeholder in [
        ("full_image_path", "storage/evidence/CH-TEST-0001_full_placeholder.jpg"),
        ("rider_image_path", "storage/evidence/CH-TEST-0001_rider_placeholder.jpg"),
        ("plate_image_path", "storage/evidence/CH-TEST-0001_plate_placeholder.jpg")
    ]:
        val = d.get(img_key) or ""
        if val:
            fname = os.path.basename(str(val))
            target = os.path.join(EVIDENCE_DIR, fname)
            if os.path.exists(target):
                d[img_key] = f"storage/evidence/{fname}"
            else:
                d[img_key] = placeholder
        else:
            d[img_key] = placeholder

    # PDF path
    pdf_val = d.get("pdf_path") or ""
    if pdf_val:
        pdf_fname = os.path.basename(str(pdf_val))
        target_pdf = os.path.join(CHALLANS_DIR, pdf_fname)
        if os.path.exists(target_pdf):
            d["pdf_path"] = f"storage/challans/{pdf_fname}"
        else:
            d["pdf_path"] = "storage/challans/CH-TEST-0001.pdf"
    else:
        d["pdf_path"] = "storage/challans/CH-TEST-0001.pdf"

    return d


def get_all_violations(limit: int = 200, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if status_filter and status_filter != "All":
        cursor.execute("SELECT * FROM violations WHERE status = ? ORDER BY id DESC LIMIT ?", (status_filter, limit))
    else:
        cursor.execute("SELECT * FROM violations ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [format_row_for_web(row) for row in rows]


def get_violation_by_id(challan_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM violations WHERE challan_id = ?", (challan_id,))
    row = cursor.fetchone()
    conn.close()
    return format_row_for_web(row) if row else None


def get_violations_by_plate(plate_number: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    clean_plate = plate_number.replace(" ", "").upper()
    cursor.execute(
        "SELECT * FROM violations WHERE REPLACE(UPPER(plate_number), ' ', '') LIKE ? ORDER BY id DESC",
        (f"%{clean_plate}%",)
    )
    rows = cursor.fetchall()
    conn.close()
    return [format_row_for_web(row) for row in rows]


def update_violation_status(challan_id: str, new_status: str, notes: str = "", new_plate: Optional[str] = None) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if new_plate:
            cursor.execute("""
                UPDATE violations
                SET status = ?, officer_notes = ?, plate_number = ?
                WHERE challan_id = ?
            """, (new_status, notes, new_plate, challan_id))
        else:
            cursor.execute("""
                UPDATE violations
                SET status = ?, officer_notes = ?
                WHERE challan_id = ?
            """, (new_status, notes, challan_id))
        conn.commit()
        conn.close()
        sync_to_csv()
        return True
    except Exception as e:
        conn.close()
        print(f"[SmartChallan DB] Error updating violation {challan_id}: {e}")
        return False


def get_kpis() -> Dict[str, Any]:
    """Calculates summary KPIs across all violations."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM violations")
    total_violations = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM violations WHERE status = 'Paid'")
    paid_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM violations WHERE status = 'Pending Review'")
    pending_review = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(fine_amount) FROM violations")
    total_fine_amount = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(fine_amount) FROM violations WHERE status = 'Paid'")
    recovered_fine = cursor.fetchone()[0] or 0

    conn.close()

    total_vehicles = max(total_violations * 4, 120)
    compliance_rate = round(((total_vehicles - total_violations) / total_vehicles) * 100, 1)

    return {
        "total_violations": total_violations,
        "paid_count": paid_count,
        "pending_review": pending_review,
        "total_fine_amount": total_fine_amount,
        "recovered_fine": recovered_fine,
        "total_vehicles": total_vehicles,
        "compliance_rate": compliance_rate
    }


def seed_sample_data_if_empty():
    """Populates realistic initial violations for immediate hackathon demonstration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM violations")
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0:
        return

    sample_records = [
        {
            "challan_id": "CH-20260908-1001",
            "track_id": 4,
            "timestamp": (datetime.now() - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
            "plate_number": "MH 12 AB 4592",
            "confidence": 0.94,
            "location": "Intersection 12, Ring Road North",
            "camera_id": "CAM-NORTH-04",
            "offense": "Section 129 / 194D MV Act - Riding Without Helmet",
            "fine_amount": 1000,
            "status": "Issued",
            "full_image_path": "",
            "rider_image_path": "",
            "plate_image_path": "",
            "pdf_path": "",
            "officer_notes": "Automated ByteTrack confirmed violation."
        },
        {
            "challan_id": "CH-20260908-1002",
            "track_id": 9,
            "timestamp": (datetime.now() - timedelta(minutes=32)).strftime("%Y-%m-%d %H:%M:%S"),
            "plate_number": "KA 03 HA 8812",
            "confidence": 0.88,
            "location": "Central Square Crossway",
            "camera_id": "CAM-CENTRAL-01",
            "offense": "Section 129 / 194D MV Act - Riding Without Helmet",
            "fine_amount": 1000,
            "status": "Paid",
            "full_image_path": "",
            "rider_image_path": "",
            "plate_image_path": "",
            "pdf_path": "",
            "officer_notes": "Paid via UPI QR portal."
        },
        {
            "challan_id": "CH-20260908-1003",
            "track_id": 14,
            "timestamp": (datetime.now() - timedelta(minutes=18)).strftime("%Y-%m-%d %H:%M:%S"),
            "plate_number": "IND-TMP-14",
            "confidence": 0.62,
            "location": "South Bypass Flyover Exit",
            "camera_id": "CAM-SOUTH-02",
            "offense": "Section 129 / 194D MV Act - Riding Without Helmet",
            "fine_amount": 1000,
            "status": "Pending Review",
            "full_image_path": "",
            "rider_image_path": "",
            "plate_image_path": "",
            "pdf_path": "",
            "officer_notes": "Plate partially obscured by mud - routed to operator review queue."
        },
        {
            "challan_id": "CH-20260908-1004",
            "track_id": 22,
            "timestamp": (datetime.now() - timedelta(minutes=12)).strftime("%Y-%m-%d %H:%M:%S"),
            "plate_number": "DL 01 CD 7731",
            "confidence": 0.91,
            "location": "Intersection 12, Ring Road North",
            "camera_id": "CAM-NORTH-04",
            "offense": "Section 129 / 194D MV Act - Riding Without Helmet",
            "fine_amount": 1000,
            "status": "Issued",
            "full_image_path": "",
            "rider_image_path": "",
            "plate_image_path": "",
            "pdf_path": "",
            "officer_notes": "SMS dispatch triggered to registered mobile."
        },
        {
            "challan_id": "CH-20260908-1005",
            "track_id": 29,
            "timestamp": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
            "plate_number": "GJ 06 KL 9024",
            "confidence": 0.96,
            "location": "Tech Hub Junction East",
            "camera_id": "CAM-EAST-03",
            "offense": "Section 129 / 194D MV Act - Riding Without Helmet",
            "fine_amount": 1000,
            "status": "Contested",
            "full_image_path": "",
            "rider_image_path": "",
            "plate_image_path": "",
            "pdf_path": "",
            "officer_notes": "Citizen requested photographic re-audit."
        }
    ]

    for rec in sample_records:
        insert_violation(**rec)
