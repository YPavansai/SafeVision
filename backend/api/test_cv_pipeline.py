import os
import cv2
import numpy as np
from django.test import TestCase
from api.cv.yolo_detector import SafetyYOLOv8Detector
from api.cv.media_processor import MediaProcessor
from api.cv.tracker import ByteTrackWorkerTracker

class SafetyDetectionPipelineTestCase(TestCase):
    """
    Unit and integration tests for SafeVision YOLOv8 detection,
    PPE-to-worker association, capability handling, and video tracking.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.detector = SafetyYOLOv8Detector()
        cls.processor = MediaProcessor()

    def test_model_loaded_and_classes_inspected(self):
        """Verifies model loading, architecture class count, and capability mapping."""
        self.assertIsNotNone(self.detector.yolo, "YOLO model should be loaded")
        self.assertGreater(len(self.detector.model_classes), 0, "Model classes should be non-empty")
        
        # Verify genuine capabilities of yolov8n.pt (COCO-80)
        self.assertTrue(self.detector.supported_capabilities['worker'], "Worker (Person) must be supported in COCO")
        self.assertTrue(self.detector.supported_capabilities['machinery'], "Machinery (Truck/Car) must be supported in COCO")
        
        # Verify that unsupported classes are correctly identified as False in COCO-80
        self.assertFalse(self.detector.supported_capabilities['helmet'], "Helmet is not in standard COCO-80")
        self.assertFalse(self.detector.supported_capabilities['safety_vest'], "Safety Vest is not in standard COCO-80")
        self.assertFalse(self.detector.supported_capabilities['gloves'], "Safety Gloves is not in standard COCO-80")
        self.assertFalse(self.detector.supported_capabilities['boots'], "Safety Boots is not in standard COCO-80")
        self.assertFalse(self.detector.supported_capabilities['fire'], "Fire is not in standard COCO-80")
        self.assertFalse(self.detector.supported_capabilities['smoke'], "Smoke is not in standard COCO-80")

    def test_real_worker_image_detection(self):
        """Tests inference on actual construction worker photo without fabricated results."""
        real_img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media', 'images', 'real_construction_worker.jpg')
        self.assertTrue(os.path.exists(real_img_path), "Sample real image should exist")
        
        img = cv2.imread(real_img_path)
        annotated_img, detections, violations, workers_analysis = self.detector.detect_image(img, confidence_threshold=0.40)
        
        # Genuine YOLOv8n detects 'person' mapped to 'Worker'
        worker_dets = [d for d in detections if d['label'] == 'Worker']
        self.assertGreater(len(worker_dets), 0, "YOLOv8n must detect worker on real construction photo")
        self.assertGreaterEqual(worker_dets[0]['confidence'], 40.0, "Confidence should meet threshold")
        
        # Ensure no unsupported violations (gloves, boots, fire) are fabricated
        fabricated_violations = [v for v in violations if v['type'] in ['Gloves Missing', 'Boots Missing', 'Fire Hazard']]
        self.assertEqual(len(fabricated_violations), 0, "Detector must never fabricate violations for unsupported classes")

    def test_ppe_to_worker_association_algorithm(self):
        """Tests the anatomical PPE-to-worker association logic directly."""
        img_shape = (600, 800)
        
        # Mock Worker: center of image [x1, y1, x2, y2]
        workers = [
            {'box': [300, 100, 500, 500], 'confidence': 92.0, 'label': 'Worker'}
        ]
        
        # Mock PPE items:
        # Helmet in head region [350, 90, 450, 180] -> center (400, 135) is inside head region [280, 80, 520, 228]
        # Safety Vest in torso region [320, 220, 480, 420] -> center (400, 320) is inside torso region
        ppe_items = [
            {'box': [350, 90, 450, 180], 'confidence': 95.0, 'label': 'Helmet'},
            {'box': [320, 220, 480, 420], 'confidence': 91.0, 'label': 'Safety Vest'}
        ]
        
        # Temporarily enable capability flags to test association logic
        orig_caps = dict(self.detector.supported_capabilities)
        self.detector.supported_capabilities['helmet'] = True
        self.detector.supported_capabilities['safety_vest'] = True
        
        try:
            analyzed = self.detector.associate_ppe_to_workers(workers, ppe_items, img_shape)
            self.assertEqual(len(analyzed), 1)
            w = analyzed[0]
            
            # Check Helmet matched
            self.assertEqual(w['ppe']['helmet']['status'], 'Compliant')
            self.assertEqual(w['ppe']['helmet']['detection']['box'], [350, 90, 450, 180])
            
            # Check Vest matched
            self.assertEqual(w['ppe']['vest']['status'], 'Compliant')
            self.assertEqual(w['ppe']['vest']['detection']['box'], [320, 220, 480, 420])
            
            # Overall compliance
            self.assertEqual(w['compliance_status'], 'Compliant')
        finally:
            self.detector.supported_capabilities = orig_caps

    def test_missing_ppe_and_truncation_handling(self):
        """Tests missing PPE detection vs uncertain truncated cases."""
        img_shape = (600, 800)
        
        # Worker 1: Fully visible, NO helmet
        # Worker 2: Head truncated at image boundary (y1 == 0)
        workers = [
            {'box': [100, 100, 250, 450], 'confidence': 88.0, 'label': 'Worker'},
            {'box': [500, 0, 650, 400], 'confidence': 85.0, 'label': 'Worker'}
        ]
        ppe_items = []
        
        orig_caps = dict(self.detector.supported_capabilities)
        self.detector.supported_capabilities['helmet'] = True
        
        try:
            analyzed = self.detector.associate_ppe_to_workers(workers, ppe_items, img_shape)
            w1 = analyzed[0]
            w2 = analyzed[1]
            
            # Worker 1 should be flagged Missing
            self.assertEqual(w1['ppe']['helmet']['status'], 'Missing')
            self.assertEqual(w1['compliance_status'], 'Non-Compliant')
            
            # Worker 2 has head cut off by image edge (wy1 <= 2) -> Uncertain, not false violation
            self.assertEqual(w2['ppe']['helmet']['status'], 'Uncertain')
            
            # Evaluate violations
            violations = self.detector.evaluate_safety_violations(analyzed, [])
            # Should have violation for Worker #1 only
            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0]['worker_id'], 'Worker #1')
            self.assertEqual(violations[0]['type'], 'Helmet Missing')
        finally:
            self.detector.supported_capabilities = orig_caps

    def test_multi_worker_disambiguation(self):
        """Tests that PPE is assigned to the correct individual worker, not all workers."""
        img_shape = (600, 800)
        workers = [
            {'box': [100, 100, 250, 450], 'confidence': 90.0, 'label': 'Worker'},
            {'box': [400, 100, 550, 450], 'confidence': 90.0, 'label': 'Worker'}
        ]
        # Only Worker 1 has a helmet
        ppe_items = [
            {'box': [140, 95, 210, 160], 'confidence': 94.0, 'label': 'Helmet'}
        ]
        
        orig_caps = dict(self.detector.supported_capabilities)
        self.detector.supported_capabilities['helmet'] = True
        
        try:
            analyzed = self.detector.associate_ppe_to_workers(workers, ppe_items, img_shape)
            self.assertEqual(analyzed[0]['ppe']['helmet']['status'], 'Compliant')
            self.assertEqual(analyzed[1]['ppe']['helmet']['status'], 'Missing')
            
            violations = self.detector.evaluate_safety_violations(analyzed, [])
            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0]['worker_id'], 'Worker #2')
        finally:
            self.detector.supported_capabilities = orig_caps

    def test_bytetrack_tracking(self):
        """Verifies ByteTrack tracker persistence and track ID assignment."""
        tracker = ByteTrackWorkerTracker()
        
        # Frame 0
        detections_f0 = [{'label': 'Worker', 'confidence': 88.0, 'box': [100, 100, 200, 300]}]
        tracked_f0, count_f0 = tracker.update(detections_f0, frame_num=0)
        self.assertEqual(len(tracked_f0), 1)
        self.assertEqual(tracked_f0[0]['track_id'], 'W-001')
        
        # Frame 1: Worker moves slightly
        detections_f1 = [{'label': 'Worker', 'confidence': 89.0, 'box': [105, 102, 205, 302]}]
        tracked_f1, count_f1 = tracker.update(detections_f1, frame_num=1)
        self.assertEqual(len(tracked_f1), 1)
        # Should keep same track ID W-001
        self.assertEqual(tracked_f1[0]['track_id'], 'W-001')
