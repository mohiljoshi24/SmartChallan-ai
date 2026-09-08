# 🚦 SmartChallan AI
### Autonomous Vision-Based Helmet Violation & Traffic Enforcement System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![YOLOv8](https://img.shields.io/badge/model-YOLOv8--Nano-green.svg)](https://github.com/ultralytics/ultralytics)
[![PyTorch](https://img.shields.io/badge/backend-PyTorch-red.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

SmartChallan AI transforms standard municipal CCTV and traffic surveillance cameras into an autonomous, 24/7 road safety enforcement network. It detects motorcycle helmet non-compliance and overcapacity (triple-riding), tracks vehicles across frames using ByteTrack, extracts registration numbers via ANPR, and autonomously compiles legally valid digital PDF E-Challans with photographic evidence.

---

## 🚨 The Problem & Market Gap

* **44%+ Road Fatalities:** Two-wheelers account for over 44% of fatal urban traffic accidents, with head trauma being the leading cause of death.
* **Flaws in Existing Computer Vision Models:**
  1. **Pedestrian False Positives:** Naive models flag walking pedestrians on sidewalks without helmets.
  2. **Alert Spamming (No Tracking):** A bike waiting at a red light triggers 30+ duplicate alerts per second.
  3. **Zero Legal Actionability:** Detecting "no helmet" is useless without reading the vehicle's **license plate** to issue a legal fine.

---

## ⚡ Our Solution & Core Pipeline

```
[ Live CCTV / RTSP / Video Feed ]
                 │
                 ▼
[ Stage 1: Hierarchical Bounding-Box Detection ]
  ├── Detects Motorcycle & Rider (Spatial IoU > 0.40)
  ├── Ignores Walkers on Sidewalks (Zero Pedestrian False Alarms)
  └── Evaluates Head Area: [Helmet] vs. [NO HELMET]
                 │
                 ▼
[ Stage 2: ByteTrack Multi-Object Tracking ]
  ├── Assigns Persistent Track ID (e.g., Bike #14)
  └── Temporal De-duplication: Enforces 1 Vehicle = 1 E-Challan Ticket
                 │
                 ▼ (If Violation Verified)
[ Stage 3: Automated License Plate Recognition (ANPR) ]
  ├── Isolates Rear Plate Region & Preprocesses (CLAHE)
  └── Character Extraction via Deep-Learning OCR (EasyOCR)
                 │
                 ▼
[ Stage 4: Court-Ready PDF E-Challan & QR Code Generation ]
  ├── Tri-Panel Proof: (1) Full Scene, (2) Rider Crop, (3) Plate Crop
  └── Scannable Instant Payment QR Code (Parivahan / UPI Gateway)
                 │
                 ▼
[ Stage 5: Municipal Command Center & Public Portal ]
  ├── Live Telemetry Stream & Alert Ticker
  ├── City Enforcement BI & Peak-Hour Analytics
  ├── Officer ANPR Review & Verification Queue
  └── Public Citizen E-Challan Payment Portal
```

---

## 🛠️ Tech Stack & Dependencies

* **Language:** Python 3.10 - 3.14
* **Deep Learning Framework:** PyTorch & Ultralytics YOLOv8 (YOLOv8 Nano - 6.2 MB)
* **Tracking Algorithm:** ByteTrack (Kalman Filter + Hungarian Association)
* **Computer Vision:** OpenCV (`cv2`)
* **OCR / ANPR:** EasyOCR (CRAFT Text Detector + ResNet + BiLSTM + CTC)
* **Document Engine:** `fpdf2` & `qrcode`
* **Web UI & APIs:** Flask, Streamlit, HTML5/CSS3/JavaScript (Dark Glassmorphic UI)
* **Database:** SQLite & Pandas CSV Audit Mirror

---

## 📁 Project Directory Structure

```text
SmartChallan ai/
│
├── core/
│   ├── database.py          # SQLite database & audit logs
│   ├── detector.py          # Hierarchical bike-rider spatial matching & triple riding
│   ├── tracker.py           # ByteTrack tracking & temporal de-duplication
│   ├── anpr.py              # License plate isolation & EasyOCR extraction
│   └── challan_generator.py # Court-ready PDF generator with scannable QR code
│
├── frontend/                # Complete multi-page web portal
│   ├── index.html           # Command Hub landing page
│   ├── live_surveillance.html # Real-time camera video stream
│   ├── challan_registry.html  # Searchable violation database & evidence modals
│   ├── analytics_dashboard.html # Chart.js business intelligence & safety stats
│   ├── anpr_review.html     # Human-in-the-loop officer plate verification queue
│   ├── citizen_portal.html  # Citizen payment gateway & UPI QR codes
│   └── system_settings.html # Edge RTSP camera & model threshold settings
│
├── storage/
│   ├── evidence/            # Saved photographic proof crops
│   ├── challans/            # Generated official PDF E-Challans
│   ├── qr_codes/            # Scannable payment QR codes
│   └── violations.db        # SQLite database
│
├── server.py                # Flask backend server & REST API bridge
├── app.py                   # Streamlit Command Center Dashboard
├── run_cli.py               # Standalone high-speed CLI runner
├── best.pt                  # Custom fine-tuned YOLOv8 helmet model
├── yolov8n.pt               # Base YOLOv8 object detector
├── Code_Execution.mp4       # Demonstration traffic video
├── requirements.txt         # Pinned dependency manifest
└── PROJECT_BLUEPRINT.md     # Master architecture & AI handoff prompt
```

---

## 🚀 Getting Started

### 1. Run the Full Web Command Portal (Flask + Multi-Page Frontend)
```bash
python server.py
```
Open `http://127.0.0.1:5000` in your browser.

### 2. Run the Streamlit Command Center
```bash
streamlit run app.py
```

### 3. Run via Headless CLI
```bash
python run_cli.py --source Code_Execution.mp4
```
Press `q` on the video window at any time to halt execution.

---

## ⚖️ Legal & Compliance Notice
This system conforms with provisions under **Section 128 (Triple-Riding)** and **Section 129 (Protective Headgear)** of the Motor Vehicles Act, utilizing automated electronic surveillance authorized under Section 136A of the Motor Vehicles (Amendment) Act.
