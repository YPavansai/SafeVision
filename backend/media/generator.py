import cv2
import numpy as np
import os
from pathlib import Path

def create_sample_image(filepath, text, bg_color=(45, 55, 72), gear_type='full'):
    """
    Generates a realistic construction site simulation image with workers and PPE features.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    h, w = 600, 800
    img = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Gradient construction background
    for y in range(h):
        r = int(bg_color[2] * (1 - y/h) + 20 * (y/h))
        g = int(bg_color[1] * (1 - y/h) + 30 * (y/h))
        b = int(bg_color[0] * (1 - y/h) + 40 * (y/h))
        img[y, :] = (b, g, r)

    # Draw grid/scaffolding lines
    for x in range(0, w, 80):
        cv2.line(img, (x, 0), (x, h), (70, 80, 95), 1)
    for y in range(0, h, 80):
        cv2.line(img, (0, y), (w, y), (70, 80, 95), 1)

    # Draw Worker silhouette / body
    cx, cy = w // 2, h // 2 + 30
    cv2.rectangle(img, (cx - 70, cy - 80), (cx + 70, cy + 140), (80, 80, 80), -1) # Body
    cv2.circle(img, (cx, cy - 130), 45, (190, 210, 230), -1) # Face / Head

    if gear_type in ['full', 'helmet']:
        # Yellow Safety Helmet
        cv2.ellipse(img, (cx, cy - 145), (55, 25), 0, 180, 360, (0, 215, 255), -1)
        cv2.rectangle(img, (cx - 60, cy - 145), (cx + 60, cy - 135), (0, 215, 255), -1)

    if gear_type in ['full', 'vest']:
        # High-Vis Orange/Yellow Vest
        cv2.rectangle(img, (cx - 65, cy - 75), (cx + 65, cy + 80), (0, 165, 255), -1)
        # Silver Reflective Stripes
        cv2.rectangle(img, (cx - 65, cy - 30), (cx + 65, cy - 15), (220, 220, 220), -1)
        cv2.rectangle(img, (cx - 65, cy + 30), (cx + 65, cy + 45), (220, 220, 220), -1)

    if gear_type == 'fire':
        # Draw Fire/Smoke simulation
        for _ in range(120):
            fx = np.random.randint(100, 350)
            fy = np.random.randint(200, 500)
            fr = np.random.randint(15, 50)
            cv2.circle(img, (fx, fy), fr, (0, np.random.randint(100, 255), 255), -1)

    # Add text overlay title
    cv2.rectangle(img, (0, h - 50), (w, h), (15, 23, 42), -1)
    cv2.putText(img, f"SafeVision Media: {text}", (20, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imwrite(filepath, img)
    print(f"Created sample image: {filepath}")

def create_sample_video(filepath, text, gear_type='full', duration_sec=3):
    """
    Generates a realistic construction simulation video file (.mp4).
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fps = 20
    total_frames = duration_sec * fps
    w, h = 640, 480

    # Try browser-compatible fourcc codecs (H.264 / AVC1 first, fallback to mp4v)
    fourcc_options = ['avc1', 'H264', 'XVID', 'mp4v']
    out = None
    for codec in fourcc_options:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out = cv2.VideoWriter(filepath, fourcc, fps, (w, h))
            if out.isOpened():
                break
        except Exception:
            continue
    
    if out is None or not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filepath, fourcc, fps, (w, h))

    for f in range(total_frames):
        img = np.zeros((h, w, 3), dtype=np.uint8)
        # Dynamic animated background
        bg_val = int(40 + 10 * np.sin(f / 5.0))
        img[:, :] = (bg_val, bg_val + 10, bg_val + 20)

        # Draw moving construction worker
        cx = int(150 + (w - 300) * (f / total_frames))
        cy = h // 2 + 20

        # Worker Body
        cv2.rectangle(img, (cx - 50, cy - 60), (cx + 50, cy + 100), (70, 70, 70), -1)
        cv2.circle(img, (cx, cy - 100), 35, (180, 200, 220), -1)

        if gear_type in ['full', 'helmet']:
            # Animated Helmet
            cv2.ellipse(img, (cx, cy - 110), (42, 20), 0, 180, 360, (0, 215, 255), -1)
            cv2.rectangle(img, (cx - 45, cy - 110), (cx + 45, cy - 102), (0, 215, 255), -1)

        if gear_type in ['full', 'vest']:
            # Animated High-Vis Vest
            cv2.rectangle(img, (cx - 48, cy - 55), (cx + 48, cy + 60), (0, 165, 255), -1)

        if gear_type == 'fire':
            # Animated Fire Alert
            for _ in range(30):
                fx = int(w * 0.7) + np.random.randint(-40, 40)
                fy = int(h * 0.6) + np.random.randint(-60, 40)
                cv2.circle(img, (fx, fy), np.random.randint(10, 35), (0, np.random.randint(120, 255), 255), -1)

        # Video HUD overlay
        cv2.rectangle(img, (0, 0), (w, 35), (15, 23, 42), -1)
        cv2.putText(img, f"CAM-01 [LIVE]: {text} | Frame {f+1}/{total_frames}", (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 127), 1, cv2.LINE_AA)

        out.write(img)

    out.release()
    print(f"Created sample video: {filepath}")

def generate_all_media(base_dir):
    media_dir = os.path.join(base_dir, 'media')
    images_dir = os.path.join(media_dir, 'images')
    videos_dir = os.path.join(media_dir, 'videos')

    # Create Sample Images
    create_sample_image(os.path.join(images_dir, 'worker_with_helmet.jpg'), 'Worker Compliant with Helmet & Vest', gear_type='full')
    create_sample_image(os.path.join(images_dir, 'worker_without_helmet.jpg'), 'Helmet Violation Warning', gear_type='vest')
    create_sample_image(os.path.join(images_dir, 'worker_without_vest.jpg'), 'Safety Vest Violation Warning', gear_type='helmet')
    create_sample_image(os.path.join(images_dir, 'fire.jpg'), 'Critical Fire Hazard Detected', gear_type='fire')

    # Create Sample Videos
    create_sample_video(os.path.join(videos_dir, 'construction_1.mp4'), 'Zone A Main Construction Feed', gear_type='full', duration_sec=4)
    create_sample_video(os.path.join(videos_dir, 'construction_2.mp4'), 'Zone B Machinery & Crane Feed', gear_type='full', duration_sec=4)
    create_sample_video(os.path.join(videos_dir, 'helmet_violation.mp4'), 'Helmet Missing Violation Feed', gear_type='vest', duration_sec=4)
    create_sample_video(os.path.join(videos_dir, 'fire_alert.mp4'), 'Critical Fire Alarm Feed', gear_type='fire', duration_sec=4)

if __name__ == '__main__':
    backend_dir = Path(__file__).resolve().parent.parent
    generate_all_media(backend_dir)
