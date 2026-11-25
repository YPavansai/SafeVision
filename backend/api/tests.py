import os
import json
import base64
import numpy as np
import cv2
from datetime import date, datetime, timedelta

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from api.models import Worker, Attendance, Violation, AISystemConfig, SystemReport, Notification, MediaFile
from api.cv.face_recognizer import ArcFaceRecognizer


class AdminAuthTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='pavan', password='pavan', email='pavan@safevision.local')

    def test_jwt_login_success(self):
        response = self.client.post('/api/auth/token/', {
            'username': 'pavan',
            'password': 'pavan'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())

    def test_jwt_login_invalid(self):
        response = self.client.post('/api/auth/token/', {
            'username': 'pavan',
            'password': 'wrongpassword'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_admin_profile_access(self):
        token_res = self.client.post('/api/auth/token/', {'username': 'pavan', 'password': 'pavan'}, content_type='application/json')
        access_token = token_res.json()['access']
        
        response = self.client.get('/api/auth/profile/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'pavan')


class WorkerManagementTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='pavan', password='pavan')
        token_res = self.client.post('/api/auth/token/', {'username': 'pavan', 'password': 'pavan'}, content_type='application/json')
        self.token = token_res.json()['access']
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

        self.worker = Worker.objects.create(
            worker_id='W-001',
            full_name='Pavan Sai',
            phone_number='+91 9876543210',
            role='Engineer',
            department='Safety',
            joining_date=date(2025, 1, 15),
            safety_score=95
        )

    def test_list_workers(self):
        response = self.client.get('/api/workers/', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['worker_id'], 'W-001')

    def test_create_worker(self):
        payload = {
            'worker_id': 'W-009',
            'full_name': 'Rohan Das',
            'phone_number': '+91 9112233445',
            'role': 'Supervisor',
            'department': 'Civil',
            'joining_date': '2025-06-01'
        }
        response = self.client.post('/api/workers/', payload, **self.headers)
        self.assertIn(response.status_code, [200, 201])
        self.assertTrue(Worker.objects.filter(worker_id='W-009').exists())

    def test_update_worker(self):
        update_payload = {
            'role': 'Supervisor',
            'safety_score': 98
        }
        response = self.client.patch(
            f'/api/workers/{self.worker.id}/',
            json.dumps(update_payload),
            content_type='application/json',
            **self.headers
        )
        self.assertEqual(response.status_code, 200)
        self.worker.refresh_from_db()
        self.assertEqual(self.worker.safety_score, 98)

    def test_delete_worker(self):
        response = self.client.delete(f'/api/workers/{self.worker.id}/', **self.headers)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Worker.objects.filter(id=self.worker.id).exists())

    def test_worker_timeline(self):
        response = self.client.get(f'/api/workers/{self.worker.id}/timeline/', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('timeline_events', response.json())


class AttendanceTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='pavan', password='pavan')
        token_res = self.client.post('/api/auth/token/', {'username': 'pavan', 'password': 'pavan'}, content_type='application/json')
        self.token = token_res.json()['access']
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

        fe = ArcFaceRecognizer()
        photo_path = 'media/worker_photos/WhatsApp_Image_2025-07-11_at_21.29.52_17af1a63.jpg'
        if os.path.exists(photo_path):
            worker_img = cv2.imread(photo_path)
            _, emb = fe.extract_embedding(worker_img)
            _, buffer = cv2.imencode('.jpg', worker_img)
            self.b64_frame = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
        else:
            canvas = np.zeros((200, 200, 3), dtype=np.uint8)
            canvas[:, :] = (180, 200, 220)
            cv2.circle(canvas, (100, 100), 50, (100, 150, 200), -1)
            _, emb = fe.extract_embedding(canvas, allow_fallback=True)
            _, buffer = cv2.imencode('.jpg', canvas)
            self.b64_frame = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

        self.worker = Worker.objects.create(
            worker_id='W-001',
            full_name='Pavan Sai',
            phone_number='+91 9876543210',
            role='Engineer',
            department='Safety',
            joining_date=date(2025, 1, 15),
            safety_score=95,
            face_encoding=emb
        )

    def test_mark_attendance_entry(self):
        response = self.client.post('/api/attendance/mark/', {
            'photo_base64': self.b64_frame,
            'type': 'entry',
            'simulate_worker_id': 'W-001'
        }, content_type='application/json', **self.headers)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json())
        self.assertTrue(Attendance.objects.filter(worker=self.worker, status='Present').exists())

    def test_duplicate_checkin_prevention(self):
        # Entry 1
        self.client.post('/api/attendance/mark/', {
            'photo_base64': self.b64_frame,
            'type': 'entry',
            'simulate_worker_id': 'W-001'
        }, content_type='application/json', **self.headers)

        # Entry 2 (Duplicate)
        res2 = self.client.post('/api/attendance/mark/', {
            'photo_base64': self.b64_frame,
            'type': 'entry',
            'simulate_worker_id': 'W-001'
        }, content_type='application/json', **self.headers)

        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.json().get('already_checked_in', False))

    def test_mark_attendance_exit_duration(self):
        # First entry
        self.client.post('/api/attendance/mark/', {
            'photo_base64': self.b64_frame,
            'type': 'entry',
            'simulate_worker_id': 'W-001'
        }, content_type='application/json', **self.headers)

        # Then exit
        res = self.client.post('/api/attendance/mark/', {
            'photo_base64': self.b64_frame,
            'type': 'exit',
            'simulate_worker_id': 'W-001'
        }, content_type='application/json', **self.headers)

        self.assertEqual(res.status_code, 200)
        att = Attendance.objects.get(worker=self.worker)
        self.assertEqual(att.status, 'Completed')
        self.assertIsNotNone(att.exit_time)

    def test_attendance_no_face_detected(self):
        # Send empty black frame without simulate_worker_id
        blank = np.zeros((200, 200, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', blank)
        b64_blank = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

        res = self.client.post('/api/attendance/mark/', {
            'photo_base64': b64_blank,
            'type': 'entry'
        }, content_type='application/json', **self.headers)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get('status'), 'NoFace')

    def test_attendance_unknown_intruder_alert(self):
        res = self.client.post('/api/attendance/mark/', {
            'photo_base64': self.b64_frame,
            'type': 'entry',
            'simulate_worker_id': 'UNKNOWN_DEMO'
        }, content_type='application/json', **self.headers)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get('status'), 'Unrecognized')
        self.assertTrue(Violation.objects.filter(source_file='CCTV / Biometric Kiosk').exists())


class ImageAnalysisAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='pavan', password='pavan')
        token_res = self.client.post('/api/auth/token/', {'username': 'pavan', 'password': 'pavan'}, content_type='application/json')
        self.token = token_res.json()['access']
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    def test_analyze_image_sample_file(self):
        response = self.client.post('/api/analysis/image/', {
            'image_name': 'real_construction_worker.jpg'
        }, content_type='application/json', **self.headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('detections', data)
        self.assertIn('safety_score', data)
        self.assertIn('output_url', data)
        self.assertGreaterEqual(data['total_objects'], 1)

    def test_analyze_image_valid_file_upload(self):
        # Create a valid JPEG in memory
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        img[:, :] = (100, 150, 200)
        _, encoded = cv2.imencode('.jpg', img)
        upload_file = SimpleUploadedFile("test_site.jpg", encoded.tobytes(), content_type="image/jpeg")

        response = self.client.post('/api/analysis/image/', {
            'image': upload_file
        }, **self.headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('detections', data)
        self.assertIn('safety_score', data)
        self.assertTrue(MediaFile.objects.filter(file_name='test_site.jpg').exists())

    def test_analyze_image_unsupported_format(self):
        dummy_file = SimpleUploadedFile("script.txt", b"print('hello world')", content_type="text/plain")
        response = self.client.post('/api/analysis/image/', {
            'image': dummy_file
        }, **self.headers)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Unsupported image format', response.json().get('error', ''))

    def test_analyze_image_corrupted_file(self):
        corrupt_file = SimpleUploadedFile("corrupt.jpg", b"NOT_A_VALID_JPEG_HEADER_BYTES", content_type="image/jpeg")
        response = self.client.post('/api/analysis/image/', {
            'image': corrupt_file
        }, **self.headers)

        self.assertEqual(response.status_code, 400)
        self.assertIn('corrupted', response.json().get('error', '').lower())

    def test_analyze_image_missing_sample(self):
        response = self.client.post('/api/analysis/image/', {
            'image_name': 'does_not_exist_file.jpg'
        }, content_type='application/json', **self.headers)

        self.assertEqual(response.status_code, 404)


class AISystemAndAnalysisTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='pavan', password='pavan')
        token_res = self.client.post('/api/auth/token/', {'username': 'pavan', 'password': 'pavan'}, content_type='application/json')
        self.token = token_res.json()['access']
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    def test_system_status_endpoint(self):
        response = self.client.get('/api/system/status/', **self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['yolov8'], 'ONLINE')
        self.assertEqual(data['arcface'], 'ONLINE')
        self.assertEqual(data['bytetrack'], 'ONLINE')
        self.assertEqual(data['database'], 'ONLINE')

    def test_dashboard_stats_endpoint(self):
        response = self.client.get('/api/dashboard/stats/', **self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_workers', data)
        self.assertIn('average_safety_score', data)
        self.assertIn('charts', data)

    def test_media_list_endpoint(self):
        response = self.client.get('/api/analysis/media/', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('videos', response.json())
        self.assertIn('images', response.json())

    def test_analyze_video_frame_endpoint(self):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', frame)
        b64_frame = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

        response = self.client.post('/api/analysis/video-frame/', {
            'photo_base64': b64_frame,
            'frame_num': 0
        }, content_type='application/json', **self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('frame_b64', response.json())
        self.assertIn('tracked_workers', response.json())


class ViolationsAndReportsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='pavan', password='pavan')
        token_res = self.client.post('/api/auth/token/', {'username': 'pavan', 'password': 'pavan'}, content_type='application/json')
        self.token = token_res.json()['access']
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

        self.violation = Violation.objects.create(
            violation_id='ALT-101',
            violation_type='Helmet Missing',
            severity='High',
            source_file='construction_1.mp4',
            status='Pending'
        )

    def test_list_violations(self):
        response = self.client.get('/api/violations/', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_resolve_violation(self):
        response = self.client.post(f'/api/violations/{self.violation.id}/resolve/', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.violation.refresh_from_db()
        self.assertEqual(self.violation.status, 'Resolved')

    def test_generate_csv_report(self):
        response = self.client.post('/api/reports/', {
            'report_type': 'daily_attendance',
            'file_format': 'csv'
        }, content_type='application/json', **self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('download_url', response.json())

    def test_generate_excel_report(self):
        response = self.client.post('/api/reports/', {
            'report_type': 'violations_export',
            'file_format': 'xlsx'
        }, content_type='application/json', **self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('download_url', response.json())
        self.assertTrue(response.json()['download_url'].endswith('.xlsx'))

    def test_list_reports(self):
        # Generate one report
        self.client.post('/api/reports/', {
            'report_type': 'worker_activity',
            'file_format': 'csv'
        }, content_type='application/json', **self.headers)

        response = self.client.get('/api/reports/', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()), 1)
