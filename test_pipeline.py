"""
SmartChallan AI - Quick Pipeline Test Script
Verifies database, PDF generation, ANPR, and model loading.
"""

import os
import sys
import numpy as np

print("Testing core imports...")
from core.database import init_db, seed_sample_data_if_empty, get_all_violations, get_kpis
from core.challan_generator import generate_challan_pdf
from core.anpr import read_license_plate, extract_plate_roi
from core.detector import HierarchicalHelmetDetector

print("1. Testing database and seeding...")
init_db()
seed_sample_data_if_empty()
viols = get_all_violations()
kpis = get_kpis()
print(f"   Database OK: {len(viols)} violations loaded, Total Fine: INR {kpis['total_fine_amount']}")

print("2. Testing PDF Challan Generation...")
test_pdf = generate_challan_pdf(
    challan_id="CH-TEST-0001",
    track_id=99,
    timestamp="2026-09-08 14:30:00",
    plate_number="MH 12 AB 1234",
    confidence=0.92,
    location="Test Intersection, Cyber City",
    camera_id="CAM-TEST-01"
)
print(f"   PDF Generation OK: File created at {test_pdf} (exists: {os.path.exists(test_pdf)})")

print("3. Testing ANPR with dummy plate ROI...")
dummy_crop = np.zeros((80, 200, 3), dtype=np.uint8)
plate_text, conf = read_license_plate(dummy_crop, track_id=99)
print(f"   ANPR Fallback/Read OK: Plate '{plate_text}' with confidence {conf}")

print("4. Testing Hierarchical Helmet Detector initialization...")
detector = HierarchicalHelmetDetector()
print("   Detector models initialized successfully!")

print("\n--- ALL PIPELINE CHECKS PASSED! ---")
