"""
SmartChallan AI - Multi-Object ByteTrack Vehicle Tracker & De-duplication Cache
Assigns persistent IDs to vehicles, tracks helmet violations across consecutive frames,
and prevents alert spamming (Enforces 1 Vehicle = 1 Violation Event).
"""

import os
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Set, List, Optional, Any
from ultralytics import YOLO

from core.anpr import extract_plate_roi, read_license_plate
from core.challan_generator import generate_challan_pdf
from core.database import insert_violation

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(BASE_DIR, "storage", "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)


class VehicleViolationTracker:
    """
    Tracks motorcycles across frames using ByteTrack, counts consecutive
    NO HELMET detections, and dispatches single E-Challans upon confirmation.
    """
    def __init__(
        self,
        consecutive_frames_thresh: int = 3,
        camera_id: str = "CAM-NORTH-04",
        location: str = "Intersection 12, Ring Road North"
    ):
        self.consecutive_frames_thresh = consecutive_frames_thresh
        self.camera_id = camera_id
        self.location = location

        # ByteTrack YOLO model restricted to motorcycle class (3)
        self.tracker_model = YOLO("yolov8n.pt")

        # Session tracking state
        self.consecutive_no_helmet: Dict[int, int] = {}
        self.processed_track_ids: Set[int] = set()
        self.total_tracked_vehicles: Set[int] = set()
        self.recent_violations: List[Dict[str, Any]] = []

    def reset_session(self):
        """Resets the tracking cache for a new video stream."""
        self.consecutive_no_helmet.clear()
        self.processed_track_ids.clear()
        self.total_tracked_vehicles.clear()
        self.recent_violations.clear()

    def process_frame(
        self,
        frame: np.ndarray,
        hierarchical_result: Dict[str, Any],
        frame_idx: int = 0
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Takes raw frame + hierarchical detection results:
        1. Tracks motorcycles using ByteTrack to get persistent track IDs.
        2. Matches tracked motorcycles with hierarchical rider/helmet state.
        3. Updates consecutive violation counters.
        4. Issues digital E-Challans for newly confirmed violations.
        5. Annotates the frame with bounding boxes, track IDs, and alert badges.
        """
        annotated = frame.copy()
        new_violations = []

        # 1. Run ByteTrack tracking on motorcycles (class 3)
        track_results = self.tracker_model.track(
            frame,
            persist=True,
            classes=[3],  # Motorcycle
            tracker="bytetrack.yaml",
            verbose=False,
            conf=0.35
        )[0]

        tracked_bikes = []
        if track_results.boxes is not None and track_results.boxes.id is not None:
            t_boxes = track_results.boxes.xyxy.cpu().numpy()
            t_ids = track_results.boxes.id.cpu().numpy().astype(int)
            t_confs = track_results.boxes.conf.cpu().numpy()

            for box, track_id, conf in zip(t_boxes, t_ids, t_confs):
                x1, y1, x2, y2 = map(int, box)
                self.total_tracked_vehicles.add(track_id)
                tracked_bikes.append({
                    "track_id": track_id,
                    "box": (x1, y1, x2, y2),
                    "conf": float(conf)
                })

        # 2. Match tracked bikes with hierarchical detector results
        motorcyclists = hierarchical_result.get("motorcyclists", [])

        for tb in tracked_bikes:
            t_id = tb["track_id"]
            tb_box = tb["box"]

            # Find corresponding hierarchical motorcycle unit
            matched_unit = None
            best_iou = 0.0
            for unit in motorcyclists:
                ub_box = unit["bike_box"]
                # Calculate simple IOU
                ix1 = max(tb_box[0], ub_box[0])
                iy1 = max(tb_box[1], ub_box[1])
                ix2 = min(tb_box[2], ub_box[2])
                iy2 = min(tb_box[3], ub_box[3])
                if ix2 > ix1 and iy2 > iy1:
                    inter = (ix2 - ix1) * (iy2 - iy1)
                    union = ((tb_box[2] - tb_box[0]) * (tb_box[3] - tb_box[1])) + \
                            ((ub_box[2] - ub_box[0]) * (ub_box[3] - ub_box[1])) - inter
                    iou = inter / float(union) if union > 0 else 0
                    if iou > best_iou:
                        best_iou = iou
                        matched_unit = unit

            helmet_status = matched_unit.get("helmet_status", "UNKNOWN") if matched_unit else "UNKNOWN"
            helmet_conf = matched_unit.get("helmet_conf", 0.0) if matched_unit else 0.0
            rider_box = matched_unit.get("rider_box") if matched_unit else None

            # 3. Update violation streak
            if helmet_status == "NO HELMET":
                self.consecutive_no_helmet[t_id] = self.consecutive_no_helmet.get(t_id, 0) + 1
            else:
                # Gradual decay or reset
                self.consecutive_no_helmet[t_id] = 0

            # 4. Check for newly confirmed violation
            is_confirmed_violation = (
                self.consecutive_no_helmet.get(t_id, 0) >= self.consecutive_frames_thresh and
                t_id not in self.processed_track_ids
            )

            if is_confirmed_violation:
                self.processed_track_ids.add(t_id)

                # Generate timestamp & unique Challan ID
                now = datetime.now()
                ts_str = now.strftime("%Y-%m-%d %H:%M:%S")
                challan_id = f"CH-{now.strftime('%Y%m%d')}-{t_id:04d}"

                # Extract crops for evidence
                bx1, by1, bx2, by2 = tb_box
                bike_crop = frame[max(0, by1):min(frame.shape[0], by2), max(0, bx1):min(frame.shape[1], bx2)]

                # Plate extraction & OCR
                plate_roi = extract_plate_roi(bike_crop)
                plate_text, ocr_conf = read_license_plate(plate_roi, track_id=t_id)

                # Save photographic evidence images
                full_img_filename = f"{challan_id}_full.jpg"
                rider_img_filename = f"{challan_id}_rider.jpg"
                plate_img_filename = f"{challan_id}_plate.jpg"

                full_img_path = os.path.join(EVIDENCE_DIR, full_img_filename)
                rider_img_path = os.path.join(EVIDENCE_DIR, rider_img_filename)
                plate_img_path = os.path.join(EVIDENCE_DIR, plate_img_filename)

                # Save full frame
                cv2.imwrite(full_img_path, frame)

                # Save rider crop
                if rider_box:
                    rx1, ry1, rx2, ry2 = rider_box
                    rider_crop = frame[max(0, ry1):min(frame.shape[0], ry2), max(0, rx1):min(frame.shape[1], rx2)]
                    if rider_crop.size > 0:
                        cv2.imwrite(rider_img_path, rider_crop)
                    else:
                        cv2.imwrite(rider_img_path, bike_crop)
                else:
                    cv2.imwrite(rider_img_path, bike_crop)

                # Save plate crop
                cv2.imwrite(plate_img_path, plate_roi if plate_roi.size > 0 else bike_crop)

                # Generate court-ready PDF E-Challan
                pdf_path = generate_challan_pdf(
                    challan_id=challan_id,
                    track_id=t_id,
                    timestamp=ts_str,
                    plate_number=plate_text,
                    confidence=helmet_conf if helmet_conf > 0 else 0.85,
                    location=self.location,
                    camera_id=self.camera_id,
                    fine_amount=1000,
                    full_image_path=full_img_path,
                    rider_image_path=rider_img_path,
                    plate_image_path=plate_img_path
                )

                # Persist to database
                insert_violation(
                    challan_id=challan_id,
                    track_id=t_id,
                    timestamp=ts_str,
                    plate_number=plate_text,
                    confidence=helmet_conf if helmet_conf > 0 else 0.85,
                    location=self.location,
                    camera_id=self.camera_id,
                    offense="Section 129 / 194D MV Act - Riding Without Helmet",
                    fine_amount=1000,
                    status="Issued" if "TMP" not in plate_text else "Pending Review",
                    full_image_path=full_img_path,
                    rider_image_path=rider_img_path,
                    plate_image_path=plate_img_path,
                    pdf_path=pdf_path,
                    officer_notes="Autonomous ByteTrack multi-frame verified detection."
                )

                violation_record = {
                    "challan_id": challan_id,
                    "track_id": t_id,
                    "timestamp": ts_str,
                    "plate_number": plate_text,
                    "confidence": helmet_conf,
                    "location": self.location,
                    "camera_id": self.camera_id,
                    "pdf_path": pdf_path,
                    "plate_img_path": plate_img_path,
                    "rider_img_path": rider_img_path,
                    "status": "Issued" if "TMP" not in plate_text else "Pending Review"
                }
                new_violations.append(violation_record)
                self.recent_violations.insert(0, violation_record)

            # 5. Visual Annotations on frame
            bx1, by1, bx2, by2 = tb_box
            is_fined = t_id in self.processed_track_ids

            if is_fined:
                color = (0, 0, 230)  # Bright Red
                status_text = f"VIOLATION FINED | Track #{t_id}"
            elif helmet_status == "NO HELMET":
                color = (0, 140, 255)  # Orange (Pending threshold)
                streak = self.consecutive_no_helmet.get(t_id, 0)
                status_text = f"NO HELMET ({streak}/{self.consecutive_frames_thresh}) | #{t_id}"
            elif helmet_status == "Helmet":
                color = (0, 200, 0)  # Green
                status_text = f"HELMET OK | Track #{t_id}"
            else:
                color = (200, 200, 0)  # Yellow/Cyan
                status_text = f"Bike #{t_id}"

            # Motorcycle bounding box
            cv2.rectangle(annotated, (bx1, by1), (bx2, by2), color, 2)

            # Rider box & spatial link
            if rider_box:
                rx1, ry1, rx2, ry2 = rider_box
                cv2.rectangle(annotated, (rx1, ry1), (rx2, ry2), (255, 200, 0), 1)
                # Spatial link line connecting rider center to bike center
                rcx = (rx1 + rx2) // 2
                rcy = (ry1 + ry2) // 2
                bcx = (bx1 + bx2) // 2
                bcy = (by1 + by2) // 2
                cv2.line(annotated, (rcx, rcy), (bcx, bcy), (255, 255, 0), 1, cv2.LINE_AA)

            # Label banner
            label_size, _ = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.rectangle(annotated, (bx1, max(0, by1 - 22)), (bx1 + label_size[0] + 8, max(22, by1)), color, -1)
            cv2.putText(annotated, status_text, (bx1 + 4, max(16, by1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

        return annotated, new_violations
