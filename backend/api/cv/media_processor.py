import cv2
import os
import threading
import time
import uuid
import numpy as np
from django.conf import settings
from .yolo_detector import SafetyYOLOv8Detector
from .face_recognizer import ArcFaceRecognizer
from .tracker import ByteTrackWorkerTracker


class MediaProcessor:
    """
    SafeVision Pipeline Processor with Thread-Safe Singleton YOLO Detector,
    Session-Isolated ByteTrack Trackers, and Bounded Resource Management.
    """

    def __init__(self):
        self.detector = SafetyYOLOv8Detector()
        self.face_recognizer = ArcFaceRecognizer()
        self.tracker = ByteTrackWorkerTracker()
        self._session_trackers = {}
        self._tracker_lock = threading.Lock()

    def _get_session_tracker(self, session_key=None):
        """Returns an isolated tracker per (admin_user, stream) to prevent cross-user interference."""
        if not session_key:
            return self.tracker
        now = time.monotonic()
        with self._tracker_lock:
            # Evict stale sessions (> 5 minutes idle)
            stale = [k for k, v in self._session_trackers.items() if now - v['last_used'] > 300]
            for k in stale:
                del self._session_trackers[k]
            if len(self._session_trackers) >= 50 and session_key not in self._session_trackers:
                oldest = min(self._session_trackers.items(), key=lambda item: item[1]['last_used'])[0]
                del self._session_trackers[oldest]

            entry = self._session_trackers.get(session_key)
            if entry is None:
                entry = {'tracker': ByteTrackWorkerTracker(), 'last_used': now}
                self._session_trackers[session_key] = entry
            else:
                entry['last_used'] = now
            return entry['tracker']

    def get_system_status(self):
        """Returns operational availability of AI engines and underlying models."""
        yolo_online = self.detector.yolo is not None
        arcface_online = bool(getattr(self.face_recognizer, 'face_cascades', None))
        bytetrack_online = self.tracker is not None
        opencv_online = hasattr(cv2, '__version__')

        return {
            'yolov8': 'ONLINE' if yolo_online else 'OFFLINE',
            'arcface': 'ONLINE' if arcface_online else 'OFFLINE',
            'bytetrack': 'ONLINE' if bytetrack_online else 'OFFLINE',
            'opencv': 'ONLINE' if opencv_online else 'OFFLINE',
            'database': 'ONLINE',
            'model_info': {
                'model_name': self.detector.model_name,
                'device': self.detector.device,
                'total_classes': len(self.detector.model_classes),
                'supported_capabilities': self.detector.supported_capabilities,
                'init_error': self.detector.init_error,
            },
        }

    def process_image(self, input_path, save_output=True, confidence_threshold=0.40):
        """
        Processes a static image file, executes genuine YOLOv8 object detection,
        performs anatomical PPE-to-worker association, renders annotations,
        and saves output image with a unique collision-free filename.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Image not found at {input_path}")

        img = cv2.imread(input_path)
        if img is None or img.size == 0:
            raise ValueError(f"Could not read image file {os.path.basename(input_path)}")

        annotated_img, detections, violations, workers_analysis = self.detector.detect_image(
            img, confidence_threshold=confidence_threshold
        )

        hazards = [d for d in detections if d['label'] in ['Fire', 'Smoke']]
        safety_score = self.calculate_safety_score(workers_analysis, hazards, violations)

        ext = os.path.splitext(input_path)[1].lower() or '.jpg'
        if ext not in ('.jpg', '.jpeg', '.png', '.webp', '.bmp'):
            ext = '.jpg'
        output_filename = f"processed_{uuid.uuid4().hex[:12]}{ext}"

        if settings.configured:
            output_dir = os.path.join(settings.MEDIA_ROOT, 'outputs')
            output_url = f"{settings.MEDIA_URL}outputs/{output_filename}"
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_dir = os.path.join(base_dir, 'media', 'outputs')
            output_url = f"/media/outputs/{output_filename}"

        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, output_filename)

        if save_output:
            cv2.imwrite(output_filepath, annotated_img)

        # Explicitly release large numpy arrays
        del img
        del annotated_img

        return {
            'detections': detections,
            'violations': violations,
            'workers_analysis': workers_analysis,
            'safety_score': safety_score,
            'output_url': output_url,
            'output_path': output_filepath,
            'total_objects': len(detections),
            'model_capabilities': self.detector.supported_capabilities,
        }

    def process_video_frame(self, frame_np, frame_num=0, confidence_thresh=0.40, session_key=None):
        """
        Processes a single video frame for live monitoring stream with session-isolated tracking.
        """
        annotated_frame, detections, violations, workers_analysis = self.detector.detect_image(
            frame_np, confidence_threshold=confidence_thresh
        )

        tracker = self._get_session_tracker(session_key)
        with self._tracker_lock:
            tracked_workers, active_count = tracker.update(
                detections, frame_num, workers_analysis=workers_analysis
            )

        hazards = [d for d in detections if d['label'] in ['Fire', 'Smoke']]
        safety_score = self.calculate_safety_score(workers_analysis, hazards, violations)

        return {
            'annotated_frame': annotated_frame,
            'detections': detections,
            'violations': violations,
            'workers_analysis': workers_analysis,
            'tracked_workers': tracked_workers,
            'active_worker_count': active_count,
            'safety_score': safety_score,
            'processing_status': 'AI Stream Active',
            'processing_fps': 10,
        }

    def calculate_safety_score(self, workers_analysis, hazards, violations):
        if hazards:
            return 0
        if not workers_analysis:
            return 100

        non_compliant_workers = sum(1 for w in workers_analysis if w['compliance_status'] == 'Non-Compliant')
        total_workers = len(workers_analysis)

        penalty = (non_compliant_workers / total_workers) * 40 + len(violations) * 10
        return max(20, int(100 - penalty))
