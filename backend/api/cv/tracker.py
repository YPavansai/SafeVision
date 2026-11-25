import numpy as np

class ByteTrackWorkerTracker:
    """
    ByteTrack Multi-Worker Tracking Engine for SafeVision
    Tracks workers across video frames, assigns persistent tracking IDs (e.g. W-001),
    and removes inactive tracks after a grace period.
    """
    def __init__(self, max_stale_frames=30):
        self.next_track_id = 1
        self.active_tracks = {} # track_id -> {'box': [x1, y1, x2, y2], 'last_seen': frame_num, 'status': str}
        self.max_stale_frames = max_stale_frames

    def update(self, detections, frame_num, workers_analysis=None):
        """
        Updates worker tracking state with current frame detections.
        """
        worker_dets = [d for d in detections if d['label'] == 'Worker']
        current_tracked = []
        matched_tracks = set()

        # Build map from box tuple to compliance status
        status_map = {}
        if workers_analysis:
            for w in workers_analysis:
                status_map[tuple(w['box'])] = w.get('compliance_status', 'Unverified')

        for det in worker_dets:
            x1, y1, x2, y2 = det['box']
            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0
            w_area = (x2 - x1) * (y2 - y1)

            matched_id = None
            min_dist = float('inf')

            for tid, tinfo in self.active_tracks.items():
                if tid in matched_tracks:
                    continue
                tx1, ty1, tx2, ty2 = tinfo['box']
                tc_x = (tx1 + tx2) / 2.0
                tc_y = (ty1 + ty2) / 2.0

                dist = np.hypot(center_x - tc_x, center_y - tc_y)
                
                # Check spatial distance and bounding box proximity
                if dist < 150.0 and dist < min_dist:
                    min_dist = dist
                    matched_id = tid

            if matched_id is None:
                matched_id = self.next_track_id
                self.next_track_id += 1

            matched_tracks.add(matched_id)
            c_status = status_map.get(tuple(det['box']), det.get('compliance_status', 'Unverified'))

            self.active_tracks[matched_id] = {
                'box': [x1, y1, x2, y2],
                'last_seen': frame_num,
                'status': c_status
            }

            current_tracked.append({
                'track_id': f"W-{matched_id:03d}",
                'box': [x1, y1, x2, y2],
                'confidence': det['confidence'],
                'compliance_status': c_status
            })

        # Remove stale tracks that haven't appeared in recent frames
        stale_ids = [
            tid for tid, tinfo in self.active_tracks.items()
            if abs(frame_num - tinfo['last_seen']) > self.max_stale_frames
        ]
        for sid in stale_ids:
            del self.active_tracks[sid]

        return current_tracked, len(self.active_tracks)

    def reset(self):
        """Resets tracking state for new video feeds or live sessions."""
        self.next_track_id = 1
        self.active_tracks.clear()
