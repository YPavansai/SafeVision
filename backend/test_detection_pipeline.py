import os
import cv2
import json
from api.cv.media_processor import MediaProcessor

def main():
    processor = MediaProcessor()
    detector = processor.detector
    
    print("=" * 65)
    print("SAFEVISION YOLOV8N DETECTION SYSTEM - COMPLETE AUDIT REPORT")
    print("=" * 65)
    
    print("\n1. MODEL INSPECTION & SUPPORTED CLASSES:")
    print(f"  Model Name:       {detector.model_name}")
    print(f"  Model Path:       {detector.model_path}")
    print(f"  Inference Device: {detector.device.upper()}")
    print(f"  Total Classes:    {len(detector.model_classes)}")
    print(f"  Model Architecture: YOLOv8n (nano PyTorch weights)")
    
    print("\n2. CAPABILITY VERIFICATION STATUS:")
    for cap, supported in detector.supported_capabilities.items():
        status = "GENUINELY SUPPORTED" if supported else "NOT IN MODEL WEIGHTS (Requires Retraining)"
        print(f"  - {cap.capitalize():<15}: {status}")

    print("\n3. STATIC IMAGE INFERENCE RESULTS:")
    images_dir = os.path.join(os.path.dirname(__file__), 'media', 'images')
    for img_name in sorted(os.listdir(images_dir)):
        if not img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        img_path = os.path.join(images_dir, img_name)
        res = processor.process_image(img_path, save_output=False, confidence_threshold=0.40)
        
        print(f"\n  Image: {img_name}")
        print(f"    Total Objects Detected: {res['total_objects']}")
        for d in res['detections']:
            print(f"      * {d['label']} | Conf: {d['confidence']}% | Box: {d['box']}")
        if res['violations']:
            print(f"    Violations ({len(res['violations'])}):")
            for v in res['violations']:
                print(f"      [!] {v['type']} ({v['severity']}) -> {v['worker_id']}: {v['detail']}")
        else:
            print(f"    Violations: None (No confirmed safety violations)")
        print(f"    Safety Score Index: {res['safety_score']}/100")

    print("\n4. REPRESENTATIVE VIDEO INFERENCE RESULTS (Frame 15):")
    videos_dir = os.path.join(os.path.dirname(__file__), 'media', 'videos')
    for vid_name in sorted(os.listdir(videos_dir)):
        if not vid_name.lower().endswith(('.mp4', '.avi')):
            continue
        vid_path = os.path.join(videos_dir, vid_name)
        cap = cv2.VideoCapture(vid_path)
        if not cap.isOpened():
            continue
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_idx = min(15, total_frames - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            continue
        
        res = processor.process_video_frame(frame, frame_num=frame_idx, confidence_thresh=0.40)
        print(f"\n  Video: {vid_name} [Frame {frame_idx}/{total_frames}]")
        print(f"    Detections: {len(res['detections'])}")
        for d in res['detections']:
            print(f"      * {d['label']} | Conf: {d['confidence']}% | Box: {d['box']}")
        print(f"    Tracked Workers: {len(res['tracked_workers'])}")
        for tw in res['tracked_workers']:
            print(f"      [Worker Track] ID: {tw['track_id']} | Status: {tw['compliance_status']}")
        print(f"    Violations: {len(res['violations'])}")
        print(f"    Safety Score: {res['safety_score']}/100")

if __name__ == '__main__':
    main()
