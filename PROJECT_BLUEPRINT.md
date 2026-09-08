## 1. PROJECT IDENTITY & HACKATHON PITCH

* **Project Name:** **SmartChallan AI**
* **Subtitle:** Autonomous Vision-Based Helmet Violation Detection & Instant E-Challan Issuance System
* **Domain / Category:** Intelligent Transportation Systems (ITS) | Smart City AI | Edge Computer Vision
* **Tagline:** Turning standard city traffic cameras into autonomous, 24/7 road-safety enforcement agents.

### The 30-Second Elevator Pitch (For Judges)
> *"Judges, over 44% of fatal road accidents involve two-wheelers, primarily caused by riders not wearing helmets. Traffic police cannot monitor every intersection, and existing AI surveillance models fail in real-world deployment because they trigger false alarms on walking pedestrians, spam 50 duplicate fines for a single bike at a red light, and cannot read number plates.*
> 
> *We are building **SmartChallan AI**—an autonomous edge vision pipeline that couples riders directly to their motorcycles, tracks vehicles across frames using ByteTrack so they are fined only once, extracts the license plate via deep-learning OCR, and autonomously generates a court-ready digital PDF E-Challan with photographic proof within seconds."*

### The Problem Statement (Formal Definition)
> *"To design and deploy an autonomous, real-time edge-vision pipeline capable of detecting motorcyclist helmet non-compliance, filtering out non-riders, tracking vehicles uniquely, extracting registration numbers via Automatic License Plate Recognition (ANPR), and autonomously generating tamper-proof digital E-Challans with visual evidence."*

### Why Existing Solutions Fail (The 3 Flaws)
1. **Pedestrian False Positives:** Standard YOLO models detect *heads* anywhere in the frame. A person walking on the sidewalk without a helmet is wrongfully flagged as a traffic violator.
2. **Alert Spamming (No Tracking):** Without vehicle tracking, a single motorcycle stopped at a red light triggers 30 duplicate violation alerts every second.
3. **Zero Enforcement Actionability (No Plate Reader):** Detecting a head without a helmet is useless unless you extract the vehicle's **license plate number** to issue a legal fine.

---

## 2. EXISTING REPOSITORY AUDIT & CURRENT STATE

The base repository (`AI-Helmet-Detection-main`) currently contains:
* **`best.pt` (~6.2 MB):** Ultralytics YOLOv8 Nano model (`yolov8n`) fine-tuned on the `New-HelmetDetection` dataset with 2 classes:
  * Class ID `0`: `Helmet`
  * Class ID `1`: `NO HELMET`
* **`object_track.py`:** Starter script with:
  * Raw YOLO inference loop (`conf=0.65`).
  * Simple bounding-box area filter (`area < 1500`).
  * Basic frame counter that sounds a Windows-only `winsound.Beep` after 10 consecutive frames.
  * Hardcoded reference to missing file `Traffic.mov`.
* **`Code_Execution.mp4` (~11.8 MB):** Demonstration sample video showing traffic flow with motorcycles.
* **`Project Report.pdf` & `Ways to Run.pdf`:** Baseline documentation.

---

## 3. COMPLETE TARGET ARCHITECTURE

```
                  [ LIVE VIDEO / RTSP / MP4 FEED ]
                                 │
                                 ▼
         ┌───────────────────────────────────────────────┐
         │ STEP 1: HIERARCHICAL DETECTION & FILTERING    │
         │ - YOLOv8 detects: 'motorcycle' & 'person'     │
         │ - Spatial association: Only inspect persons   │
         │   sitting on a motorcycle (Ignores walkers)   │
         │ - Crop head region -> Run 'best.pt' for:      │
         │   [Helmet] vs. [NO HELMET]                    │
         └───────────────────────┬───────────────────────┘
                                 │
                                 ▼
         ┌───────────────────────────────────────────────┐
         │ STEP 2: MULTI-OBJECT TRACKING (ByteTrack)     │
         │ - Assigns persistent Track ID (e.g. Bike #14) │
         │ - De-duplication Cache: Checks if Bike #14    │
         │   already has a registered violation ticket   │
         │ - Enforces: 1 Vehicle = 1 Violation Event     │
         └───────────────────────┬───────────────────────┘
                                 │
                                 ▼ (If NO HELMET confirmed)
         ┌───────────────────────────────────────────────┐
         │ STEP 3: AUTOMATED LICENSE PLATE READER (ANPR) │
         │ - Isolate lower half / rear of motorcycle     │
         │ - License Plate localization (YOLO / Contour) │
         │ - Alphanumeric OCR text extraction (EasyOCR)  │
         │ - Multi-frame voting for highest confidence   │
         └───────────────────────┬───────────────────────┘
                                 │
                                 ▼
         ┌───────────────────────────────────────────────┐
         │ STEP 4: AUTONOMOUS EVIDENCE & E-CHALLAN GEN   │
         │ - Save timestamped cropped evidence images:   │
         │   (1) Full frame, (2) Rider crop, (3) Plate   │
         │ - Generate official PDF E-Challan ticket      │
         │   with GPS, Time, Fine amount, and QR Code    │
         │ - Append incident to CSV/SQLite audit log     │
         └───────────────────────┬───────────────────────┘
                                 │
                                 ▼
         ┌───────────────────────────────────────────────┐
         │ STEP 5: SMART CITY WEB COMMAND DASHBOARD      │
         │ - Streamlit UI for traffic operators          │
         │ - Real-time video monitor with toggles        │
         │ - Live violation alert cards                  │
         │ - Compliance statistics (% wearing helmets)   │
         │ - Search / filter violations by plate number  │
         └───────────────────────────────────────────────┘
```

---

## 4. TECH STACK & SYSTEM DEPENDENCIES

* **Python Version:** 3.10 to 3.14 (64-bit)
* **Core Libraries:**
  * `ultralytics` (YOLOv8 inference & built-in ByteTrack/BoT-SORT)
  * `opencv-python` (Computer Vision video processing & drawing)
  * `torch` & `torchvision` (PyTorch execution engine)
  * `easyocr` (Deep learning optical character recognition for plates)
  * `fpdf2` (Lightning-fast PDF document generation for E-Challan)
  * `streamlit` (Modern interactive web dashboard for hackathon demos)
  * `pandas`, `numpy`, `pillow` (Dataframes, math, image saving)

### `requirements.txt`
```text
ultralytics>=8.0.0
opencv-python>=4.8.0
torch>=2.0.0
torchvision>=0.15.0
easyocr>=1.7.0
fpdf2>=2.7.0
streamlit>=1.30.0
pandas>=2.0.0
numpy>=1.24.0
pillow>=10.0.0
```

---

## 5. MODULAR DIRECTORY STRUCTURE TO BUILD

```text
AI-Helmet-Detection-main/
│
├── best.pt                       # Custom trained YOLOv8 helmet weights (2 classes)
├── Code_Execution.mp4            # Sample traffic video
├── requirements.txt              # Dependency definitions
├── PROJECT_BLUEPRINT.md          # Master context & AI handoff specification
│
├── core/
│   ├── __init__.py
│   ├── detector.py               # Combined detection & hierarchical rider-bike matching
│   ├── tracker.py                # ByteTrack integration for persistent ID assignment
│   ├── anpr.py                   # License plate crop & EasyOCR text reader
│   └── challan_generator.py      # Automated PDF E-Challan builder using fpdf2
│
├── storage/
│   ├── evidence/                 # Saved violation crops (full, rider, plate)
│   ├── challans/                 # Generated PDF tickets
│   └── violations.csv            # Persistent log of all detected violations
│
├── app.py                        # Streamlit web command center dashboard
└── run_cli.py                    # Lightweight standalone CLI runner
```

---

## 6. MODULE-BY-MODULE SPECIFICATIONS

### Module A: `core/detector.py`
* Load standard `yolov8n.pt` for general objects (Motorcycle: Class `3`, Person: Class `0`).
* Load custom `best.pt` for helmet states (`0: Helmet`, `1: NO HELMET`).
* Spatial Association Algorithm:
  * For each detected person box $B_p$, calculate vertical and horizontal overlap with any detected motorcycle box $B_m$.
  * If $\text{overlap}(B_p, B_m) > 0.4$, classify person as **Motorcyclist**.
  * Only run helmet classification on confirmed Motorcyclists.

### Module B: `core/tracker.py`
* Run `model.track(frame, persist=True, tracker="bytetrack.yaml")`.
* Maintain a session set `processed_track_ids = set()`.
* If a tracked vehicle exhibits `NO HELMET` confidence above threshold across $N$ consecutive frames:
  * Trigger single violation event.
  * Add `track_id` to `processed_track_ids`.

### Module C: `core/anpr.py`
* Locate the lower 30% of the motorcycle bounding box.
* Apply basic image pre-processing (grayscale, contrast normalization).
* Run `easyocr.Reader(['en'])` to extract alphanumeric plate text.
* Clean string using regex: `re.sub(r'[^A-Z0-9]', '', raw_text)`.
* Fallback to `"IND-TMP-" + str(track_id)` if plate is unreadable due to severe blur.

### Module D: `core/challan_generator.py`
* Uses `fpdf2` to create a clean A4 E-Challan:
  * Header: "MUNICIPAL TRAFFIC POLICE DEPARTMENT — E-CHALLAN"
  * Incident Details: Date, Time, Camera ID (`CAM-NORTH-04`), Location (`Intersection 12`).
  * Violation Type: Section 129 Motor Vehicles Act (Riding without protective headgear).
  * Fine Amount: ₹1,000 / $50.00.
  * Embedded Images:
    * Frame Snapshot (Full vehicle context)
    * Zoomed Rider Crop (Showing head without helmet)
    * Zoomed License Plate Crop (Showing registration number)

### Module E: `app.py` (Streamlit Dashboard)
* **Left Column:** Live video playback stream with rendered bounding boxes, track labels, and violation markers.
* **Right Column:** Real-time violation ticker:
  * Dynamic cards showing recent violators with their plate number, time, and a **"Download E-Challan PDF"** button.
* **Bottom Metrics:**
  * Total Vehicles Processed | Violations Detected | Helmet Compliance Rate %

---

## 7. JUDGES Q&A DEFENSE CHEAT SHEET

* **Q: How do you prevent flagging pedestrians walking on sidewalks?**
  * *Answer:* "We use hierarchical spatial association. We detect motorcycles first, locate the rider relative to the bike bounding box, and only trigger helmet inference on validated riders."
* **Q: How do you prevent duplicate fines at red lights?**
  * *Answer:* "We integrate ByteTrack multi-object tracking. Each vehicle retains a single persistent Track ID, and our de-duplication cache ensures exactly one violation record is logged per vehicle ID."
* **Q: How does this perform on low-cost edge devices?**
  * *Answer:* "Both YOLOv8 Nano and ByteTrack are ultra-lightweight (~6 MB model size), achieving 25–30 FPS on standard CPUs without requiring expensive enterprise GPUs."
