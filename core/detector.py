"""
SmartChallan AI - Hierarchical Rider-Motorcycle Detector & Helmet Classifier
Prevents false positives on pedestrians by spatially associating detected persons
with motorcycles, only classifying helmet compliance on verified motorcyclists.
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_HELMET_MODEL = os.path.join(BASE_DIR, "best.pt")
DEFAULT_GENERAL_MODEL = "yolov8n.pt"


def calculate_overlap_ratio(box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int]) -> float:
    """
    Calculates the intersection area normalized by the smaller box (box_a = person).
    box format: (x1, y1, x2, y2)
    """
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])

    if x2 <= x1 or y2 <= y1:
        return 0.0

    inter_area = (x2 - x1) * (y2 - y1)
    area_a = max((box_a[2] - box_a[0]) * (box_a[3] - box_a[1]), 1)
    return inter_area / float(area_a)


class HierarchicalHelmetDetector:
    """
    Hierarchical vision pipeline:
    1. Detects persons (Class 0) and motorcycles (Class 3) via YOLOv8n.
    2. Filters out pedestrians by enforcing spatial overlap with motorcycles.
    3. Evaluates helmet compliance on confirmed motorcyclists using fine-tuned best.pt.
    """
    def __init__(
        self,
        general_model_name: str = DEFAULT_GENERAL_MODEL,
        helmet_model_path: str = DEFAULT_HELMET_MODEL,
        conf_thresh: float = 0.45,
        overlap_thresh: float = 0.30
    ):
        self.conf_thresh = conf_thresh
        self.overlap_thresh = overlap_thresh

        # Load models
        print(f"[SmartChallan Detector] Loading general model: {general_model_name}")
        self.general_model = YOLO(general_model_name)

        print(f"[SmartChallan Detector] Loading helmet model: {helmet_model_path}")
        if os.path.exists(helmet_model_path):
            self.helmet_model = YOLO(helmet_model_path)
        else:
            print(f"[SmartChallan Detector] Warning: {helmet_model_path} not found. Fallback to general model.")
            self.helmet_model = self.general_model

    def detect_and_associate(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Executes hierarchical detection on a single video frame.
        Returns:
            - motorcyclists: List of dicts with rider, bike, helmet status, and crops
            - pedestrians_ignored: Count of pedestrians on sidewalks ignored
            - raw_detections: Raw boxes for debugging
        """
        h_frame, w_frame = frame.shape[:2]

        # 1. Detect general objects (Person: 0, Motorcycle: 3)
        gen_results = self.general_model(frame, conf=self.conf_thresh, verbose=False)[0]

        persons = []
        motorcycles = []

        if gen_results.boxes is not None and len(gen_results.boxes) > 0:
            boxes = gen_results.boxes.xyxy.cpu().numpy()
            clss = gen_results.boxes.cls.cpu().numpy().astype(int)
            confs = gen_results.boxes.conf.cpu().numpy()

            for box, cls_id, conf in zip(boxes, clss, confs):
                x1, y1, x2, y2 = map(int, box)
                # Bound within frame
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w_frame, x2), min(h_frame, y2)

                if cls_id == 0:  # Person
                    persons.append({"box": (x1, y1, x2, y2), "conf": float(conf)})
                elif cls_id == 3:  # Motorcycle
                    motorcycles.append({"box": (x1, y1, x2, y2), "conf": float(conf)})

        # 2. Run custom helmet model on frame (or head regions)
        helmet_results = self.helmet_model(frame, conf=0.20, verbose=False)[0]
        helmet_detections = []
        if helmet_results.boxes is not None and len(helmet_results.boxes) > 0:
            h_boxes = helmet_results.boxes.xyxy.cpu().numpy()
            h_clss = helmet_results.boxes.cls.cpu().numpy().astype(int)
            h_confs = helmet_results.boxes.conf.cpu().numpy()
            for hbox, hcls, hconf in zip(h_boxes, h_clss, h_confs):
                hx1, hy1, hx2, hy2 = map(int, hbox)
                helmet_detections.append({
                    "box": (hx1, hy1, hx2, hy2),
                    "cls": int(hcls),  # 0: Helmet, 1: NO HELMET
                    "label": "Helmet" if int(hcls) == 0 else "NO HELMET",
                    "conf": float(hconf)
                })

        # 3. Spatial Association: Associate Person <-> Motorcycle
        motorcyclists = []
        matched_persons = set()

        for bike_idx, bike in enumerate(motorcycles):
            b_box = bike["box"]
            best_person = None
            max_overlap = 0.0

            for p_idx, person in enumerate(persons):
                p_box = person["box"]
                # Calculate spatial overlap
                overlap = calculate_overlap_ratio(p_box, b_box)

                # Posture & positioning verification:
                # 1. Rider head/torso should be positioned predominantly in the upper half of the bike
                # 2. Rider bottom (feet/hips) should not extend far below the motorcycle wheels
                # 3. Rider center must align horizontally with motorcycle
                p_cx = (p_box[0] + p_box[2]) / 2.0
                p_height = p_box[3] - p_box[1]
                b_height = b_box[3] - b_box[1]
                
                # Check if person is seated on the bike rather than standing behind/away
                is_centered = (b_box[0] - 15 <= p_cx <= b_box[2] + 15)
                # Head must be above the bike's bottom half, and feet cannot be far below the bike
                is_seated_vertically = (p_box[1] < b_box[1] + 0.40 * b_height) and (p_box[3] <= b_box[3] + 0.20 * b_height)
                
                # Enforce either significant geometric overlap (seated rider) OR clean seated vertical alignment with reasonable overlap
                if is_centered and is_seated_vertically and (overlap >= 0.22):
                    if overlap > max_overlap:
                        max_overlap = overlap
                        best_person = (p_idx, person)

            # Determine helmet state for the confirmed rider
            rider_box = best_person[1]["box"] if best_person else None
            if best_person:
                matched_persons.add(best_person[0])

            # Classify helmet status for this motorcycle unit
            helmet_status = "UNKNOWN"
            helmet_conf = 0.0
            head_crop = None
            rider_crop = None

            if rider_box:
                rx1, ry1, rx2, ry2 = rider_box
                rider_crop = frame[ry1:ry2, rx1:rx2].copy()

                # Approximate head region: upper 40% of rider bounding box
                head_y2 = ry1 + int((ry2 - ry1) * 0.45)
                head_box = (rx1, ry1, rx2, head_y2)
                if head_y2 > ry1:
                    head_crop = frame[ry1:head_y2, rx1:rx2].copy()

                # Check if any helmet detection matches this head region
                matched_helmet = None
                for hd in helmet_detections:
                    h_box = hd["box"]
                    # Check overlap between helmet detection and head region
                    h_overlap = calculate_overlap_ratio(h_box, head_box)
                    if h_overlap > 0.15 or calculate_overlap_ratio(h_box, rider_box) > 0.15:
                        matched_helmet = hd
                        break

                if matched_helmet:
                    helmet_status = matched_helmet["label"]
                    helmet_conf = matched_helmet["conf"]
                else:
                    # Direct inference on head crop if no global match
                    if head_crop is not None and head_crop.shape[0] > 15 and head_crop.shape[1] > 15:
                        sub_res = self.helmet_model(head_crop, conf=0.18, verbose=False)[0]
                        if sub_res.boxes is not None and len(sub_res.boxes) > 0:
                            s_cls = int(sub_res.boxes.cls.cpu().numpy()[0])
                            s_conf = float(sub_res.boxes.conf.cpu().numpy()[0])
                            helmet_status = "Helmet" if s_cls == 0 else "NO HELMET"
                            helmet_conf = s_conf
                        else:
                            # A rider with a visible head but NO helmet detected is a violator (NO HELMET)
                            helmet_status = "NO HELMET"
                            helmet_conf = 0.65
                    else:
                        helmet_status = "NO HELMET"
                        helmet_conf = 0.55
            else:
                # Motorcycle detected without an isolated person box (e.g. at distance or occlusion)
                # Check if any helmet detection is inside the upper half of the bike
                bx1, by1, bx2, by2 = b_box
                upper_bike = (bx1, by1, bx2, by1 + int((by2 - by1) * 0.5))
                for hd in helmet_detections:
                    if calculate_overlap_ratio(hd["box"], upper_bike) > 0.15:
                        helmet_status = hd["label"]
                        helmet_conf = hd["conf"]
                        break

            # Bike crop for plate reader
            bx1, by1, bx2, by2 = b_box
            bike_crop = frame[by1:by2, bx1:bx2].copy() if (by2 > by1 and bx2 > bx1) else None

            motorcyclists.append({
                "bike_box": b_box,
                "rider_box": rider_box,
                "has_rider": (rider_box is not None),
                "helmet_status": helmet_status,
                "helmet_conf": helmet_conf,
                "bike_crop": bike_crop,
                "rider_crop": rider_crop,
                "head_crop": head_crop
            })

        pedestrians_ignored = len(persons) - len(matched_persons)

        return {
            "motorcyclists": motorcyclists,
            "pedestrians_ignored": max(pedestrians_ignored, 0),
            "total_motorcycles": len(motorcycles),
            "total_persons": len(persons),
            "helmet_detections": helmet_detections
        }
