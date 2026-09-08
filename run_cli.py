"""
SmartChallan AI - Standalone Command Line Interface (CLI) Runner
Runs the full vision pipeline headlessly on video files or RTSP streams.
"""

import os
import sys
import time
import argparse
import cv2

from core.detector import HierarchicalHelmetDetector
from core.tracker import VehicleViolationTracker
from core.database import init_db, get_kpis


def run_pipeline(
    video_source: str = "Code_Execution.mp4",
    output_path: str = None,
    conf_thresh: float = 0.45,
    overlap_thresh: float = 0.30,
    camera_id: str = "CAM-NORTH-04",
    location: str = "Intersection 12, Ring Road North",
    max_frames: int = 0
):
    print("=" * 65)
    print("     SMARTCHALLAN AI - AUTONOMOUS EDGE ENFORCEMENT RUNNER      ")
    print("=" * 65)
    print(f"[Config] Video Source    : {video_source}")
    print(f"[Config] Camera ID       : {camera_id}")
    print(f"[Config] Location        : {location}")
    print(f"[Config] Confidence Thresh: {conf_thresh}")
    print(f"[Config] Overlap Thresh  : {overlap_thresh}")

    init_db()

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"[Error] Failed to open video source: {video_source}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        print(f"[Config] Saving annotated video to: {output_path}")

    detector = HierarchicalHelmetDetector(conf_thresh=conf_thresh, overlap_thresh=overlap_thresh)
    tracker = VehicleViolationTracker(camera_id=camera_id, location=location)

    frame_idx = 0
    t_start = time.time()
    violations_count = 0

    print("\n[Status] Pipeline active. Processing frames...\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            if max_frames > 0 and frame_idx > max_frames:
                print(f"[Status] Reached maximum requested frames ({max_frames}).")
                break

            # 1. Hierarchical detection
            h_result = detector.detect_and_associate(frame)

            # 2. Tracking & violation management
            annotated_frame, new_viols = tracker.process_frame(frame, h_result, frame_idx=frame_idx)

            if new_viols:
                for v in new_viols:
                    violations_count += 1
                    print(f"🚨 [VIOLATION CONFIRMED] Challan #{v['challan_id']} | Plate: {v['plate_number']} | Track: #{v['track_id']} | PDF: {os.path.basename(v['pdf_path'])}")

            if writer:
                writer.write(annotated_frame)

            if frame_idx % 25 == 0:
                elapsed = time.time() - t_start
                cur_fps = frame_idx / max(elapsed, 0.001)
                print(f"[Progress] Frame {frame_idx}/{total_frames} | Speed: {cur_fps:.1f} FPS | Active Vehicles: {len(tracker.total_tracked_vehicles)} | Violations: {violations_count}")

    except KeyboardInterrupt:
        print("\n[Status] Interrupted by user.")

    finally:
        cap.release()
        if writer:
            writer.release()

    elapsed = time.time() - t_start
    avg_fps = frame_idx / max(elapsed, 0.001)
    print("\n" + "=" * 65)
    print("                    PIPELINE SUMMARY                           ")
    print("=" * 65)
    print(f"Total Frames Processed : {frame_idx}")
    print(f"Total Execution Time   : {elapsed:.2f} seconds")
    print(f"Average Speed          : {avg_fps:.1f} FPS")
    print(f"Unique Vehicles Tracked: {len(tracker.total_tracked_vehicles)}")
    print(f"Violations Logged      : {violations_count}")
    print(f"Compliance Rate        : {tracker.total_tracked_vehicles and round(((len(tracker.total_tracked_vehicles)-violations_count)/len(tracker.total_tracked_vehicles))*100, 1)}%")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SmartChallan AI CLI Runner")
    parser.add_argument("--video", type=str, default="Code_Execution.mp4", help="Path to input video or RTSP url")
    parser.add_argument("--out", type=str, default=None, help="Path to save annotated video")
    parser.add_argument("--conf", type=float, default=0.45, help="Detection confidence threshold")
    parser.add_argument("--overlap", type=float, default=0.30, help="Spatial overlap threshold for rider-bike pairing")
    parser.add_argument("--camera-id", type=str, default="CAM-NORTH-04", help="Surveillance camera ID")
    parser.add_argument("--location", type=str, default="Intersection 12, Ring Road North", help="Camera location name")
    parser.add_argument("--max-frames", type=int, default=0, help="Stop after N frames (0 for entire video)")

    args = parser.parse_args()
    run_pipeline(
        video_source=args.video,
        output_path=args.out,
        conf_thresh=args.conf,
        overlap_thresh=args.overlap,
        camera_id=args.camera_id,
        location=args.location,
        max_frames=args.max_frames
    )
