"""
SmartChallan AI - Unified Backend Server & API Bridge
Connects the HTML/CSS/JS frontend pages to the core computer vision models,
SQLite database, PDF generator, and live video stream.
"""

import os
import cv2
import json
import time
import threading
from werkzeug.utils import secure_filename
from flask import Flask, send_from_directory, jsonify, request, Response
from flask_cors import CORS

from core.database import (
    init_db, seed_sample_data_if_empty, get_all_violations,
    get_violation_by_id, get_violations_by_plate, update_violation_status,
    get_kpis, EVIDENCE_DIR, CHALLANS_DIR, STORAGE_DIR, BASE_DIR
)
from core.challan_generator import generate_challan_pdf
from core.detector import HierarchicalHelmetDetector
from core.tracker import VehicleViolationTracker

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "frontend"))
CORS(app)

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")
PROCESSED_DIR = os.path.join(STORAGE_DIR, "processed")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

DEFAULT_VIDEO = os.path.abspath(os.path.join(BASE_DIR, "Code_Execution.mp4"))

# Global streaming state
active_video_path = DEFAULT_VIDEO
stream_version = 0
stream_lock = threading.Lock()

stream_stats = {
    "fps": 0.0,
    "active_bikes": 0,
    "wearing_helmet": 0,
    "no_helmet": 0,
    "pedestrians_filtered": 0,
    "total_violations": 0,
    "current_frame": 0,
    "total_frames": 0,
    "active_video": "Code_Execution.mp4",
    "is_running": False
}

# Global detector & tracker instances
_detector = None
_tracker = None

def get_vision_pipeline():
    global _detector, _tracker
    if _detector is None:
        _detector = HierarchicalHelmetDetector()
    if _tracker is None:
        _tracker = VehicleViolationTracker()
    return _detector, _tracker


# 1. Serve Frontend HTML Pages
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def serve_static_page(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


# 2. Serve Storage Assets (Evidence, PDFs, Uploads, Processed Videos)
@app.route("/storage/evidence/<filename>")
def serve_evidence(filename):
    return send_from_directory(EVIDENCE_DIR, filename)

@app.route("/storage/challans/<filename>")
def serve_challan_pdf(filename):
    return send_from_directory(CHALLANS_DIR, filename)

@app.route("/storage/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(UPLOADS_DIR, filename)

@app.route("/storage/processed/<filename>")
def serve_processed(filename):
    return send_from_directory(PROCESSED_DIR, filename)


# 3. Video Upload, Available List & Source Selection
@app.route("/api/available_videos", methods=["GET"])
def api_available_videos():
    videos = []
    # 1. Default demo video
    if os.path.exists(DEFAULT_VIDEO):
        videos.append({
            "name": "Code_Execution.mp4",
            "type": "Demo Sample Video",
            "size_mb": round(os.path.getsize(DEFAULT_VIDEO) / (1024 * 1024), 1),
            "is_active": (active_video_path == DEFAULT_VIDEO)
        })

    # 2. Any videos uploaded in storage/uploads/
    for fname in os.listdir(UPLOADS_DIR):
        if fname.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
            fpath = os.path.join(UPLOADS_DIR, fname)
            videos.append({
                "name": fname,
                "type": "Uploaded Custom Video",
                "size_mb": round(os.path.getsize(fpath) / (1024 * 1024), 1),
                "is_active": (active_video_path == fpath)
            })

    return jsonify({
        "active_video": os.path.basename(active_video_path),
        "videos": videos
    })


@app.route("/api/upload_video", methods=["POST"])
def api_upload_video():
    global active_video_path, stream_version
    if "video" not in request.files:
        return jsonify({"error": "No video file provided in form-data"}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.abspath(os.path.join(UPLOADS_DIR, filename))
    file.save(save_path)

    with stream_lock:
        active_video_path = save_path
        stream_version += 1
        stream_stats["active_video"] = filename
        # Reset tracker for newly uploaded video
        if _tracker:
            _tracker.reset_session()

    print(f"[SmartChallan Server] Successfully uploaded & activated new video: {save_path}")
    return jsonify({
        "status": "success",
        "filename": filename,
        "path": save_path,
        "message": f"Video '{filename}' uploaded and set as active feed."
    })


@app.route("/api/select_video", methods=["POST"])
def api_select_video():
    global active_video_path, stream_version
    data = request.json or {}
    filename = data.get("filename", "Code_Execution.mp4")

    target_path = DEFAULT_VIDEO
    if filename != "Code_Execution.mp4":
        possible = os.path.abspath(os.path.join(UPLOADS_DIR, filename))
        if os.path.exists(possible):
            target_path = possible

    with stream_lock:
        active_video_path = target_path
        stream_version += 1
        stream_stats["active_video"] = os.path.basename(target_path)
        if _tracker:
            _tracker.reset_session()

    print(f"[SmartChallan Server] Switched active video to: {active_video_path}")
    return jsonify({"status": "success", "active_video": os.path.basename(active_video_path)})


# 4. REST APIs for Frontend Integration
@app.route("/api/kpis", methods=["GET"])
def api_kpis():
    return jsonify(get_kpis())

@app.route("/api/stream_stats", methods=["GET"])
def api_stream_stats():
    return jsonify(stream_stats)

@app.route("/api/violations", methods=["GET"])
def api_violations():
    status = request.args.get("status")
    limit = int(request.args.get("limit", 200))
    viols = get_all_violations(limit=limit, status_filter=status if status != "All" else None)
    return jsonify(viols)

@app.route("/api/violations/<challan_id>", methods=["GET"])
def api_violation_detail(challan_id):
    rec = get_violation_by_id(challan_id)
    if rec:
        return jsonify(rec)
    return jsonify({"error": "Violation citation not found"}), 404

@app.route("/api/search_plate", methods=["GET"])
def api_search_plate():
    plate = request.args.get("plate", "").strip()
    if not plate:
        return jsonify([])
    results = get_violations_by_plate(plate)
    return jsonify(results)

@app.route("/api/verify_plate", methods=["POST"])
def api_verify_plate():
    data = request.json or {}
    challan_id = data.get("challan_id")
    verified_plate = data.get("verified_plate")
    notes = data.get("notes", "Verified by officer")

    if not challan_id or not verified_plate:
        return jsonify({"error": "Missing challan_id or verified_plate"}), 400

    rec = get_violation_by_id(challan_id)
    if not rec:
        return jsonify({"error": "Record not found"}), 404

    # Regenerate official PDF with verified plate
    generate_challan_pdf(
        challan_id=rec["challan_id"],
        track_id=rec["track_id"],
        timestamp=rec["timestamp"],
        plate_number=verified_plate.upper(),
        confidence=0.99,
        location=rec["location"],
        camera_id=rec["camera_id"],
        fine_amount=rec["fine_amount"],
        full_image_path=rec.get("full_image_path", ""),
        rider_image_path=rec.get("rider_image_path", ""),
        plate_image_path=rec.get("plate_image_path", "")
    )

    update_violation_status(challan_id, "Issued", notes=notes, new_plate=verified_plate.upper())
    return jsonify({"status": "success", "message": f"Plate verified as {verified_plate.upper()}"})

@app.route("/api/dismiss_violation", methods=["POST"])
def api_dismiss():
    data = request.json or {}
    challan_id = data.get("challan_id")
    notes = data.get("notes", "Dismissed by officer as false positive")
    update_violation_status(challan_id, "Dismissed", notes=notes)
    return jsonify({"status": "success", "message": "Violation dismissed"})

@app.route("/api/pay_challan", methods=["POST"])
def api_pay():
    data = request.json or {}
    challan_id = data.get("challan_id")
    if not challan_id:
        return jsonify({"error": "Missing challan_id"}), 400
    update_violation_status(challan_id, "Paid", notes="Settled online via citizen payment gateway")
    return jsonify({"status": "success", "message": "Payment recorded"})


# 5. Live MJPEG AI Video Detection Stream with Dynamic Video Switching
def generate_frames(requested_video=None):
    global stream_stats, active_video_path, stream_version
    detector, tracker = get_vision_pipeline()

    # Determine video to play
    current_video = requested_video if requested_video and os.path.exists(requested_video) else active_video_path
    local_version = stream_version

    cap = cv2.VideoCapture(current_video)
    if not cap.isOpened():
        print(f"[SmartChallan Stream] Warning: Failed to open {current_video}. Reverting to demo.")
        current_video = DEFAULT_VIDEO
        cap = cv2.VideoCapture(current_video)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    stream_stats["total_frames"] = total_frames
    stream_stats["active_video"] = os.path.basename(current_video)
    stream_stats["is_running"] = True

    frame_idx = 0
    t_prev = time.time()

    try:
        while True:
            # Check if active video was switched by user while streaming
            if not requested_video and (current_video != active_video_path or local_version != stream_version):
                cap.release()
                current_video = active_video_path
                local_version = stream_version
                cap = cv2.VideoCapture(current_video)
                frame_idx = 0
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                stream_stats["total_frames"] = total_frames
                stream_stats["active_video"] = os.path.basename(current_video)
                print(f"[SmartChallan Stream] Switched stream to: {current_video}")

            ret, frame = cap.read()
            if not ret:
                # Loop video seamlessly from start
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_idx = 0
                continue

            frame_idx += 1

            # 1. Hierarchical detection (YOLOv8 + best.pt)
            h_res = detector.detect_and_associate(frame)

            # 2. ByteTrack multi-object tracking
            annotated_frame, new_viols = tracker.process_frame(frame, h_res, frame_idx=frame_idx)

            # 3. Calculate real-time stats
            now = time.time()
            dt = now - t_prev
            t_prev = now
            fps = round(1.0 / max(dt, 0.001), 1)

            motorcyclists = h_res.get("motorcyclists", [])
            wearing_helmet = sum(1 for m in motorcyclists if m.get("helmet_status") == "Helmet")
            no_helmet = sum(1 for m in motorcyclists if m.get("helmet_status") == "NO HELMET")

            stream_stats.update({
                "fps": min(fps, 35.0),
                "active_bikes": len(tracker.total_tracked_vehicles),
                "wearing_helmet": wearing_helmet,
                "no_helmet": no_helmet,
                "pedestrians_filtered": h_res.get("pedestrians_ignored", 0),
                "total_violations": len(tracker.processed_track_ids),
                "current_frame": frame_idx
            })

            # 4. Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.02)
    finally:
        cap.release()
        stream_stats["is_running"] = False


@app.route("/api/video_feed")
def video_feed():
    """MJPEG Video streaming route."""
    video_source = request.args.get("source")
    target_path = None
    if video_source:
        if video_source == "demo":
            target_path = DEFAULT_VIDEO
        else:
            cand = os.path.abspath(os.path.join(UPLOADS_DIR, video_source))
            if os.path.exists(cand):
                target_path = cand

    return Response(generate_frames(target_path), mimetype='multipart/x-mixed-replace; boundary=frame')


# 6. Full Batch Video Processing (Processes whole video and outputs annotated MP4)
@app.route("/api/process_video_sync", methods=["POST"])
def api_process_video_sync():
    data = request.json or {}
    filename = data.get("filename", os.path.basename(active_video_path))
    max_frames = int(data.get("max_frames", 150))

    if filename == "Code_Execution.mp4":
        input_path = DEFAULT_VIDEO
    else:
        input_path = os.path.abspath(os.path.join(UPLOADS_DIR, filename))
        if not os.path.exists(input_path):
            input_path = DEFAULT_VIDEO

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        return jsonify({"error": f"Failed to open video {input_path}"}), 400

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    output_filename = f"processed_{int(time.time())}_{secure_filename(filename)}"
    output_path = os.path.join(PROCESSED_DIR, output_filename)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    detector, tracker = get_vision_pipeline()
    tracker.reset_session()

    frame_count = 0
    t_start = time.time()
    violations_found = []

    print(f"[SmartChallan Batch] Processing video {input_path} -> {output_path} (max {max_frames} frames)...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if max_frames > 0 and frame_count > max_frames:
            break

        h_res = detector.detect_and_associate(frame)
        annotated_frame, new_viols = tracker.process_frame(frame, h_res, frame_idx=frame_count)

        if new_viols:
            violations_found.extend(new_viols)

        writer.write(annotated_frame)

    cap.release()
    writer.release()

    elapsed = round(time.time() - t_start, 2)
    print(f"[SmartChallan Batch] Completed: {frame_count} frames in {elapsed}s.")

    return jsonify({
        "status": "success",
        "output_filename": output_filename,
        "output_url": f"/storage/processed/{output_filename}",
        "frames_processed": frame_count,
        "elapsed_seconds": elapsed,
        "total_vehicles_tracked": len(tracker.total_tracked_vehicles),
        "violations_detected": len(tracker.processed_track_ids),
        "new_violations": violations_found
    })


if __name__ == "__main__":
    init_db()
    seed_sample_data_if_empty()
    print("=" * 65)
    print("      SMARTCHALLAN AI - UNIFIED BACKEND SERVER ACTIVE          ")
    print("=" * 65)
    print("  🌐 Web Dashboard : http://127.0.0.1:5000")
    print("  📹 Live Feed     : http://127.0.0.1:5000/api/video_feed")
    print("  📑 Available Vids: http://127.0.0.1:5000/api/available_videos")
    print("=" * 65)
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
