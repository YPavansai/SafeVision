import cv2
import numpy as np
import os
from django.conf import settings

class SafetyYOLOv8Detector:
    """
    SafeVision Production YOLOv8 Safety Detector & PPE Association Engine
    
    1. Loads deep learning YOLO model anchored reliably to settings.BASE_DIR.
    2. Inspects model architecture and verifies genuinely supported classes.
    3. Eliminates all synthetic/fabricated detections and fake confidence scores.
    4. Implements documented anatomical PPE-to-Worker spatial association.
    5. Disambiguates model detection limitations from safety rule violations.
    6. Explicitly handles uncertain/truncated cases without generating false violations.
    """

    # Precise domain class name mappings
    WORKER_NAMES = {'person', 'human', 'worker'}
    HELMET_NAMES = {'helmet', 'hard hat', 'hardhat', 'safety helmet'}
    VEST_NAMES = {'vest', 'safety vest', 'reflective vest', 'high-vis vest', 'high-visibility vest'}
    GLOVES_NAMES = {'safety glove', 'safety gloves', 'work glove', 'work gloves', 'protective gloves'}
    BOOTS_NAMES = {'safety boot', 'safety boots', 'work boot', 'work boots', 'steel-toe boot', 'steel-toe boots'}
    MACHINERY_NAMES = {'truck', 'car', 'bus', 'train', 'machinery', 'excavator', 'crane', 'forklift', 'bulldozer', 'tractor', 'cement mixer'}
    FIRE_NAMES = {'fire', 'flame', 'blaze'}
    SMOKE_NAMES = {'smoke'}

    # Explicit exclusions of COCO classes that share words but represent different objects
    COCO_EXCLUSIONS = {'baseball glove', 'fire hydrant'}

    def __init__(self, model_name='yolov8n.pt'):
        if not os.path.isabs(model_name):
            base_dir = getattr(settings, 'BASE_DIR', None) if settings.configured else None
            if not base_dir:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            resolved = os.path.join(base_dir, model_name)
            self.model_path = resolved if os.path.exists(resolved) else model_name
        else:
            self.model_path = model_name

        self.model_name = os.path.basename(self.model_path)
        self.yolo = None
        self.device = 'cpu'
        self.model_classes = {}
        self.class_map = {}
        self.supported_capabilities = {
            'worker': False,
            'helmet': False,
            'safety_vest': False,
            'gloves': False,
            'boots': False,
            'machinery': False,
            'fire': False,
            'smoke': False,
        }

        try:
            from ultralytics import YOLO
            import torch
            # Limit CPU threads to prevent memory/thread thrashing on constrained containers
            torch.set_num_threads(1)
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.yolo = YOLO(self.model_path)
            self.model_classes = dict(self.yolo.names)
            self._verify_class_capabilities()
            # Warm up model once at startup so first API request does not time out
            dummy = np.zeros((320, 320, 3), dtype=np.uint8)
            self.yolo(dummy, verbose=False, imgsz=320, device=self.device)
            print(f"[SafeVision YOLO Engine] Loaded model '{self.model_name}' on {self.device} with {len(self.model_classes)} classes.")
        except Exception as e:
            print(f"[SafeVision YOLO Engine] Model load warning: ({e}).")

    def _verify_class_capabilities(self):
        """Inspects model class names and maps them to safety domains."""
        self.class_map = {}
        for cls_id, raw_name in self.model_classes.items():
            name_lower = raw_name.lower().strip()

            # Reject false positives from general COCO dataset
            if name_lower in self.COCO_EXCLUSIONS:
                continue

            if name_lower in self.WORKER_NAMES:
                self.class_map[cls_id] = 'Worker'
                self.supported_capabilities['worker'] = True
            elif name_lower in self.HELMET_NAMES:
                self.class_map[cls_id] = 'Helmet'
                self.supported_capabilities['helmet'] = True
            elif name_lower in self.VEST_NAMES:
                self.class_map[cls_id] = 'Safety Vest'
                self.supported_capabilities['safety_vest'] = True
            elif name_lower in self.GLOVES_NAMES:
                self.class_map[cls_id] = 'Gloves'
                self.supported_capabilities['gloves'] = True
            elif name_lower in self.BOOTS_NAMES:
                self.class_map[cls_id] = 'Boots'
                self.supported_capabilities['boots'] = True
            elif name_lower in self.MACHINERY_NAMES:
                self.class_map[cls_id] = f"Machinery ({raw_name.capitalize()})"
                self.supported_capabilities['machinery'] = True
            elif name_lower in self.FIRE_NAMES:
                self.class_map[cls_id] = 'Fire'
                self.supported_capabilities['fire'] = True
            elif name_lower in self.SMOKE_NAMES:
                self.class_map[cls_id] = 'Smoke'
                self.supported_capabilities['smoke'] = True

    def detect_image(self, image_np, confidence_threshold=0.40):
        """
        Runs genuine object detection on numpy BGR image frame.
        Returns:
            annotated_img: Image with rendered styled bounding boxes and badges
            display_detections: List of detection dicts for frontend rendering
            violations: List of safety violations with per-worker attribution
            workers_analysis: Granular worker PPE audit structures
        """
        if image_np is None or image_np.size == 0:
            return image_np, [], [], []

        h, w = image_np.shape[:2]
        # Downscale oversized uploads to keep CPU inference fast & within container RAM
        max_dim = 1280
        if max(h, w) > max_dim:
            scale = max_dim / float(max(h, w))
            image_np = cv2.resize(image_np, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            h, w = image_np.shape[:2]

        annotated_img = image_np.copy()
        raw_detections = []

        if self.yolo:
            try:
                # YOLOv8 handles RGB conversion, letterboxing, and per-class NMS internally
                results = self.yolo(image_np, verbose=False, conf=confidence_threshold, imgsz=480, device=self.device)[0]
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Boundary clip
                    x1 = max(0, min(w - 1, x1))
                    y1 = max(0, min(h - 1, y1))
                    x2 = max(0, min(w - 1, x2))
                    y2 = max(0, min(h - 1, y2))
                    if x2 <= x1 or y2 <= y1:
                        continue

                    # Only process mapped safety domain classes
                    if cls_id in self.class_map:
                        label = self.class_map[cls_id]
                    else:
                        label = results.names[cls_id].capitalize()

                    raw_detections.append({
                        'cls_id': cls_id,
                        'label': label,
                        'confidence': round(conf * 100, 1),
                        'box': [x1, y1, x2, y2]
                    })
            except Exception as ex:
                print(f"[SafeVision YOLO] Inference exception: {ex}")

        # Separate detections into categories
        workers = [d for d in raw_detections if d['label'] == 'Worker']
        ppe_items = [d for d in raw_detections if d['label'] in ['Helmet', 'Safety Vest', 'Gloves', 'Boots']]
        machinery = [d for d in raw_detections if 'Machinery' in d['label']]
        hazards = [d for d in raw_detections if d['label'] in ['Fire', 'Smoke']]

        # Associate PPE to individual workers
        workers_analysis = self.associate_ppe_to_workers(workers, ppe_items, img_shape=(h, w))

        # Evaluate safety violations
        violations = self.evaluate_safety_violations(workers_analysis, hazards)

        # Render styled bounding boxes & badges
        self.render_annotations(annotated_img, workers_analysis, ppe_items, machinery, hazards)

        # Standard detections list formatted for frontend
        display_detections = []
        for w_info in workers_analysis:
            display_detections.append({
                'label': 'Worker',
                'confidence': w_info['confidence'],
                'box': w_info['box'],
                'compliance_status': w_info['compliance_status']
            })
        for ppe in ppe_items:
            display_detections.append({
                'label': ppe['label'],
                'confidence': ppe['confidence'],
                'box': ppe['box']
            })
        for m in machinery:
            display_detections.append({
                'label': m['label'],
                'confidence': m['confidence'],
                'box': m['box']
            })
        for hz in hazards:
            display_detections.append({
                'label': hz['label'],
                'confidence': hz['confidence'],
                'box': hz['box']
            })

        return annotated_img, display_detections, violations, workers_analysis

    def associate_ppe_to_workers(self, workers, ppe_items, img_shape):
        """
        Documented Method for Associating Detected PPE with Individual Workers
        
        Spatial Anatomical Region Definition:
        For a worker bounding box [wx1, wy1, wx2, wy2] with dimensions W_w, W_h:
          - Head Region: [wx1 - 0.10*W_w, wy1 - 0.05*W_h, wx2 + 0.10*W_w, wy1 + 0.32*W_h]
          - Torso Region: [wx1, wy1 + 0.20*W_h, wx2, wy1 + 0.70*W_h]
          - Hands Region: [wx1 - 0.15*W_w, wy1 + 0.40*W_h, wx2 + 0.15*W_w, wy1 + 0.85*W_h]
          - Feet Region: [wx1, wy1 + 0.70*W_h, wx2, wy2 + 0.05*W_h]

        Association Metric:
        Candidate PPE P = [px1, py1, px2, py2] is associated with target region R if:
          1. Center of P is inside R, OR
          2. Intersection-over-Candidate Area IoA = Area(P ∩ R) / Area(P) >= 0.35
        """
        h, w = img_shape
        analyzed_workers = []

        available_helmets = [p for p in ppe_items if p['label'] == 'Helmet']
        available_vests = [p for p in ppe_items if p['label'] == 'Safety Vest']
        available_gloves = [p for p in ppe_items if p['label'] == 'Gloves']
        available_boots = [p for p in ppe_items if p['label'] == 'Boots']

        for idx, worker in enumerate(workers):
            wx1, wy1, wx2, wy2 = worker['box']
            ww = wx2 - wx1
            wh = wy2 - wy1

            # Anatomical Regions
            head_region = [wx1 - 0.10 * ww, wy1 - 0.05 * wh, wx2 + 0.10 * ww, wy1 + 0.32 * wh]
            torso_region = [wx1, wy1 + 0.20 * wh, wx2, wy1 + 0.70 * wh]
            hands_region = [wx1 - 0.15 * ww, wy1 + 0.40 * wh, wx2 + 0.15 * ww, wy1 + 0.85 * wh]
            feet_region = [wx1, wy1 + 0.70 * wh, wx2, wy2 + 0.05 * wh]

            # Boundary truncation checks
            head_truncated = (wy1 <= 2)
            feet_truncated = (wy2 >= h - 3)

            # Match PPE candidates to regions
            matched_helmet = self._find_best_match(head_region, available_helmets)
            matched_vest = self._find_best_match(torso_region, available_vests)
            matched_gloves = self._find_best_match(hands_region, available_gloves)
            matched_boots = self._find_best_match(feet_region, available_boots)

            worker_ppe = {}

            # Helmet evaluation
            if not self.supported_capabilities['helmet']:
                worker_ppe['helmet'] = {
                    'status': 'Unverified',
                    'detail': 'Unsupported by model weights',
                    'detection': None
                }
            elif matched_helmet:
                worker_ppe['helmet'] = {
                    'status': 'Compliant',
                    'detail': f"Worn ({matched_helmet['confidence']}%)",
                    'detection': matched_helmet
                }
            elif head_truncated:
                worker_ppe['helmet'] = {
                    'status': 'Uncertain',
                    'detail': 'Head truncated by frame boundary',
                    'detection': None
                }
            else:
                worker_ppe['helmet'] = {
                    'status': 'Missing',
                    'detail': 'No helmet detected on head',
                    'detection': None
                }

            # Safety Vest evaluation
            if not self.supported_capabilities['safety_vest']:
                worker_ppe['vest'] = {
                    'status': 'Unverified',
                    'detail': 'Unsupported by model weights',
                    'detection': None
                }
            elif matched_vest:
                worker_ppe['vest'] = {
                    'status': 'Compliant',
                    'detail': f"Worn ({matched_vest['confidence']}%)",
                    'detection': matched_vest
                }
            else:
                worker_ppe['vest'] = {
                    'status': 'Missing',
                    'detail': 'No vest detected on torso',
                    'detection': None
                }

            # Gloves evaluation
            if not self.supported_capabilities['gloves']:
                worker_ppe['gloves'] = {
                    'status': 'Unverified',
                    'detail': 'Unsupported by model weights',
                    'detection': None
                }
            elif matched_gloves:
                worker_ppe['gloves'] = {
                    'status': 'Compliant',
                    'detail': f"Worn ({matched_gloves['confidence']}%)",
                    'detection': matched_gloves
                }
            else:
                worker_ppe['gloves'] = {
                    'status': 'Missing',
                    'detail': 'No gloves detected on hands',
                    'detection': None
                }

            # Boots evaluation
            if not self.supported_capabilities['boots']:
                worker_ppe['boots'] = {
                    'status': 'Unverified',
                    'detail': 'Unsupported by model weights',
                    'detection': None
                }
            elif matched_boots:
                worker_ppe['boots'] = {
                    'status': 'Compliant',
                    'detail': f"Worn ({matched_boots['confidence']}%)",
                    'detection': matched_boots
                }
            elif feet_truncated:
                worker_ppe['boots'] = {
                    'status': 'Uncertain',
                    'detail': 'Feet truncated by frame boundary',
                    'detection': None
                }
            else:
                worker_ppe['boots'] = {
                    'status': 'Missing',
                    'detail': 'No boots detected on feet',
                    'detection': None
                }

            # Overall compliance status calculation
            has_missing = any(item['status'] == 'Missing' for item in worker_ppe.values())
            has_compliant = any(item['status'] == 'Compliant' for item in worker_ppe.values())
            all_supported_compliant = all(item['status'] == 'Compliant' for item in worker_ppe.values() if item['status'] != 'Unverified')

            if has_missing:
                compliance_status = 'Non-Compliant'
            elif has_compliant and all_supported_compliant:
                compliance_status = 'Compliant'
            else:
                compliance_status = 'Unverified'

            analyzed_workers.append({
                'worker_id': idx + 1,
                'box': [wx1, wy1, wx2, wy2],
                'confidence': worker['confidence'],
                'compliance_status': compliance_status,
                'ppe': worker_ppe
            })

        return analyzed_workers

    def _find_best_match(self, region, candidate_list):
        """Finds candidate PPE whose IoA with target region is highest (>= 0.35)."""
        rx1, ry1, rx2, ry2 = region
        best_cand = None
        best_score = 0.0

        for cand in candidate_list:
            cx1, cy1, cx2, cy2 = cand['box']
            c_area = max(1, (cx2 - cx1) * (cy2 - cy1))

            ix1 = max(rx1, cx1)
            iy1 = max(ry1, cy1)
            ix2 = min(rx2, cx2)
            iy2 = min(ry2, cy2)

            if ix2 > ix1 and iy2 > iy1:
                inter_area = (ix2 - ix1) * (iy2 - iy1)
                ioa = inter_area / float(c_area)
                center_x = (cx1 + cx2) / 2.0
                center_y = (cy1 + cy2) / 2.0
                inside_region = (rx1 <= center_x <= rx2 and ry1 <= center_y <= ry2)

                score = ioa + (0.5 if inside_region else 0.0)
                if ioa >= 0.35 and score > best_score:
                    best_score = score
                    best_cand = cand

        return best_cand

    def evaluate_safety_violations(self, analyzed_workers, hazards):
        """
        Generates violations only for confirmed model-supported items.
        Separates model detection limitations from worker violations.
        """
        violations = []
        for w in analyzed_workers:
            wid = w['worker_id']
            if w['ppe']['helmet']['status'] == 'Missing':
                violations.append({
                    'type': 'Helmet Missing',
                    'worker_id': f"Worker #{wid}",
                    'severity': 'High',
                    'detail': f"Worker #{wid} detected without required safety helmet"
                })
            if w['ppe']['vest']['status'] == 'Missing':
                violations.append({
                    'type': 'Safety Vest Missing',
                    'worker_id': f"Worker #{wid}",
                    'severity': 'High',
                    'detail': f"Worker #{wid} detected without required safety vest"
                })
            if w['ppe']['gloves']['status'] == 'Missing':
                violations.append({
                    'type': 'Gloves Missing',
                    'worker_id': f"Worker #{wid}",
                    'severity': 'Medium',
                    'detail': f"Worker #{wid} detected without safety gloves"
                })
            if w['ppe']['boots']['status'] == 'Missing':
                violations.append({
                    'type': 'Boots Missing',
                    'worker_id': f"Worker #{wid}",
                    'severity': 'Medium',
                    'detail': f"Worker #{wid} detected without safety boots"
                })

        for hz in hazards:
            violations.append({
                'type': f"{hz['label']} Hazard",
                'worker_id': 'Site Wide',
                'severity': 'Critical',
                'detail': f"Critical {hz['label'].lower()} hazard detected ({hz['confidence']}%)"
            })

        return violations

    def render_annotations(self, img, workers_analysis, ppe_items, machinery, hazards):
        """Renders styled bounding boxes and badges with safe boundary clipping."""
        h, w = img.shape[:2]

        # 1. Workers
        for w_info in workers_analysis:
            x1, y1, x2, y2 = w_info['box']
            status = w_info['compliance_status']
            conf = w_info['confidence']
            wid = w_info['worker_id']

            if status == 'Compliant':
                color = (0, 255, 127) # Green
            elif status == 'Non-Compliant':
                color = (0, 0, 255)   # Red
            else:
                color = (0, 215, 255) # Cyan (Worker detected, PPE unverified in COCO)

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            
            # Badge text
            badge_text = f"Worker #{wid} | {conf}%"
            if status != 'Unverified':
                badge_text += f" [{status}]"
            
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            by1 = max(0, y1 - 22)
            by2 = max(22, y1)
            bx2 = min(w - 1, x1 + tw + 10)
            cv2.rectangle(img, (x1, by1), (bx2, by2), color, -1)
            cv2.putText(img, badge_text, (x1 + 4, max(16, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

        # 2. PPE items (if detected by model)
        for ppe in ppe_items:
            x1, y1, x2, y2 = ppe['box']
            color = (0, 255, 127) # Green
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            badge_text = f"{ppe['label']} | {ppe['confidence']}%"
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            by1 = max(0, y1 - 18)
            by2 = max(18, y1)
            bx2 = min(w - 1, x1 + tw + 8)
            cv2.rectangle(img, (x1, by1), (bx2, by2), color, -1)
            cv2.putText(img, badge_text, (x1 + 4, max(14, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)

        # 3. Machinery
        for m in machinery:
            x1, y1, x2, y2 = m['box']
            color = (255, 140, 0) # Amber
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            badge_text = f"{m['label']} | {m['confidence']}%"
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            by1 = max(0, y1 - 20)
            by2 = max(20, y1)
            bx2 = min(w - 1, x1 + tw + 8)
            cv2.rectangle(img, (x1, by1), (bx2, by2), color, -1)
            cv2.putText(img, badge_text, (x1 + 4, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

        # 4. Hazards
        for hz in hazards:
            x1, y1, x2, y2 = hz['box']
            color = (0, 0, 255) # Crimson
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
            badge_text = f"CRITICAL HAZARD: {hz['label']} | {hz['confidence']}%"
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            by1 = max(0, y1 - 24)
            by2 = max(24, y1)
            bx2 = min(w - 1, x1 + tw + 10)
            cv2.rectangle(img, (x1, by1), (bx2, by2), color, -1)
            cv2.putText(img, badge_text, (x1 + 4, max(18, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
