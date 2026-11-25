import os
import django
import sys
import csv
import cv2
import numpy as np
from datetime import date, datetime, timedelta
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safevision.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Worker, Attendance, Shift, Violation, Notification, AISystemConfig, MediaFile, SystemReport
from api.cv.face_recognizer import ArcFaceRecognizer

face_engine = ArcFaceRecognizer()

def seed():
    # 1. Default Admin User (Username: pavan, Password: pavan)
    admin_user, _ = User.objects.get_or_create(username='pavan')
    admin_user.set_password('pavan')
    admin_user.email = 'pavan@safevision.local'
    admin_user.first_name = 'Pavan'
    admin_user.last_name = 'Sai'
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    print("[Seed] Configured default Admin user (Username: pavan, Password: pavan)")

    # 2. AI Config
    AISystemConfig.objects.get_or_create(
        id=1,
        defaults={
            'processing_fps': 10,
            'confidence_threshold': 0.50,
            'frame_skip': 2
        }
    )

    # 3. Extended Indian Workers Roster
    workers_data = [
        {
            'worker_id': 'W-001',
            'full_name': 'Pavan Sai',
            'phone_number': '+91 98765 43210',
            'role': 'Engineer',
            'department': 'Safety',
            'joining_date': date(2025, 1, 15),
            'safety_score': 95,
        },
        {
            'worker_id': 'W-002',
            'full_name': 'Rajesh Kumar',
            'phone_number': '+91 98123 45678',
            'role': 'Supervisor',
            'department': 'Civil',
            'joining_date': date(2025, 2, 1),
            'safety_score': 88,
        },
        {
            'worker_id': 'W-003',
            'full_name': 'Vikram Singh',
            'phone_number': '+91 97654 32109',
            'role': 'Operator',
            'department': 'Mechanical',
            'joining_date': date(2025, 3, 10),
            'safety_score': 92,
        },
        {
            'worker_id': 'W-004',
            'full_name': 'Priya Sharma',
            'phone_number': '+91 99887 76655',
            'role': 'Electrician',
            'department': 'Electrical',
            'joining_date': date(2025, 4, 5),
            'safety_score': 100,
        },
        {
            'worker_id': 'W-005',
            'full_name': 'Amit Patel',
            'phone_number': '+91 98712 34567',
            'role': 'Laborer',
            'department': 'Civil',
            'joining_date': date(2025, 5, 12),
            'safety_score': 78,
        },
        {
            'worker_id': 'W-006',
            'full_name': 'Suresh Reddy',
            'phone_number': '+91 91234 56789',
            'role': 'Laborer',
            'department': 'Mechanical',
            'joining_date': date(2025, 6, 1),
            'safety_score': 85,
        },
        {
            'worker_id': 'W-007',
            'full_name': 'Sunita Verma',
            'phone_number': '+91 92345 67890',
            'role': 'Engineer',
            'department': 'Safety',
            'joining_date': date(2025, 6, 15),
            'safety_score': 98,
        },
        {
            'worker_id': 'W-008',
            'full_name': 'Rahul Gupta',
            'phone_number': '+91 93456 78901',
            'role': 'Operator',
            'department': 'Civil',
            'joining_date': date(2025, 7, 1),
            'safety_score': 90,
        },
    ]

    workers = []
    for wdata in workers_data:
        worker = Worker.objects.filter(worker_id=wdata['worker_id']).first()
        if not worker:
            worker = Worker.objects.create(**wdata)
        else:
            worker.full_name = wdata['full_name']
            worker.phone_number = wdata['phone_number']
            worker.role = wdata['role']
            worker.department = wdata['department']
            worker.safety_score = wdata['safety_score']
            worker.save()

        # Face ArcFace biometric embedding registration with distinct worker signatures
        dummy_face = np.zeros((160, 160, 3), dtype=np.uint8)
        idx = int(wdata['worker_id'].split('-')[1])
        b_val = 140 + (idx * 15) % 60
        g_val = 160 + (idx * 20) % 70
        r_val = 180 + (idx * 25) % 75
        dummy_face[:, :] = (b_val, g_val, r_val)
        cv2.circle(dummy_face, (80, 75), 45 - (idx % 8), (b_val - 40, g_val - 40, r_val - 40), -1) # Head
        cv2.circle(dummy_face, (60 + (idx % 6), 65), 8, (30, 30, 30), -1) # Left Eye
        cv2.circle(dummy_face, (100 - (idx % 6), 65), 8, (30, 30, 30), -1) # Right Eye
        cv2.line(dummy_face, (80, 75), (80, 95), (40, 40, 40), 3) # Nose
        cv2.ellipse(dummy_face, (80, 110 + (idx % 5)), (20 + (idx % 5), 8), 0, 0, 180, (20, 20, 120), -1) # Mouth
        
        _, embedding = face_engine.extract_embedding(dummy_face)
        if embedding:
            worker.face_encoding = embedding
            worker.save()

        workers.append(worker)
        print(f"[Seed] Processed worker {worker.full_name} ({worker.worker_id})")

    # 4. Multi-Day Attendance Records Seeding
    today = date.today()
    now = datetime.now()

    for d_offset in range(5):
        current_date = today - timedelta(days=d_offset)
        for i, w in enumerate(workers):
            if (i + d_offset) % 5 == 0:
                continue # Simulate absent day occasionally
            entry_t = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=8, minutes=(i * 12) % 45)
            exit_t = entry_t + timedelta(hours=8, minutes=15)
            
            status_val = 'Completed' if d_offset > 0 else ('Present' if i < 4 else 'Completed')
            
            Attendance.objects.get_or_create(
                worker=w,
                date=current_date,
                defaults={
                    'entry_time': entry_t,
                    'exit_time': exit_t if status_val == 'Completed' else None,
                    'total_hours': 8.25 if status_val == 'Completed' else 4.0,
                    'status': status_val
                }
            )

    print("[Seed] Seeded multi-day attendance records across workers.")

    # 5. Comprehensive Safety Violation Records Seeding
    violations_data = [
        {
            'violation_id': 'ALT-1001',
            'worker': Worker.objects.get(worker_id='W-005'), # Amit Patel
            'violation_type': 'Helmet Missing',
            'severity': 'High',
            'source_file': 'construction_1.mp4',
            'status': 'Pending',
            'confidence_score': 96.5,
        },
        {
            'violation_id': 'ALT-1002',
            'worker': Worker.objects.get(worker_id='W-006'), # Suresh Reddy
            'violation_type': 'Safety Vest Missing',
            'severity': 'Medium',
            'source_file': 'helmet_violation.mp4',
            'status': 'Resolved',
            'confidence_score': 91.2,
            'resolved_by': 'pavan'
        },
        {
            'violation_id': 'ALT-1003',
            'worker': None,
            'violation_type': 'Fire Hazard',
            'severity': 'Critical',
            'source_file': 'fire_alert.mp4',
            'status': 'Pending',
            'confidence_score': 99.1,
        },
        {
            'violation_id': 'ALT-1004',
            'worker': Worker.objects.get(worker_id='W-003'), # Vikram Singh
            'violation_type': 'Gloves Missing',
            'severity': 'Low',
            'source_file': 'construction_2.mp4',
            'status': 'Resolved',
            'confidence_score': 88.4,
            'resolved_by': 'pavan'
        },
        {
            'violation_id': 'ALT-1005',
            'worker': Worker.objects.get(worker_id='W-002'), # Rajesh Kumar
            'violation_type': 'Boots Missing',
            'severity': 'Low',
            'source_file': 'construction_1.mp4',
            'status': 'Resolved',
            'confidence_score': 89.0,
            'resolved_by': 'pavan'
        },
        {
            'violation_id': 'ALT-1006',
            'worker': Worker.objects.get(worker_id='W-008'), # Rahul Gupta
            'violation_type': 'Restricted Area',
            'severity': 'High',
            'source_file': 'Zone C Gate Kiosk',
            'status': 'Pending',
            'confidence_score': 94.8,
        },
        {
            'violation_id': 'ALT-1007',
            'worker': None,
            'violation_type': 'Unrecognized Intruder',
            'severity': 'High',
            'source_file': 'Main Check-In Kiosk',
            'status': 'Pending',
            'confidence_score': 34.2,
        },
        {
            'violation_id': 'ALT-1008',
            'worker': Worker.objects.get(worker_id='W-006'), # Suresh Reddy
            'violation_type': 'Helmet Missing',
            'severity': 'High',
            'source_file': 'construction_2.mp4',
            'status': 'Pending',
            'confidence_score': 97.0,
        },
        {
            'violation_id': 'ALT-1009',
            'worker': Worker.objects.get(worker_id='W-005'), # Amit Patel
            'violation_type': 'Safety Vest Missing',
            'severity': 'Medium',
            'source_file': 'construction_1.mp4',
            'status': 'Resolved',
            'confidence_score': 93.5,
            'resolved_by': 'pavan'
        },
        {
            'violation_id': 'ALT-1010',
            'worker': None,
            'violation_type': 'Fire Hazard',
            'severity': 'Critical',
            'source_file': 'fire.jpg',
            'status': 'Resolved',
            'confidence_score': 98.7,
            'resolved_by': 'pavan'
        },
        {
            'violation_id': 'ALT-1011',
            'worker': Worker.objects.get(worker_id='W-004'), # Priya Sharma
            'violation_type': 'Gloves Missing',
            'severity': 'Low',
            'source_file': 'Zone B Wiring',
            'status': 'Pending',
            'confidence_score': 90.5,
        },
        {
            'violation_id': 'ALT-1012',
            'worker': None,
            'violation_type': 'Unrecognized Intruder',
            'severity': 'High',
            'source_file': 'Gate Kiosk 2',
            'status': 'Pending',
            'confidence_score': 41.0,
        },
    ]

    for v_data in violations_data:
        vio_id = v_data['violation_id']
        vio = Violation.objects.filter(violation_id=vio_id).first()
        if not vio:
            vio = Violation.objects.create(
                violation_id=vio_id,
                worker=v_data['worker'],
                violation_type=v_data['violation_type'],
                severity=v_data['severity'],
                source_file=v_data['source_file'],
                status=v_data['status'],
                confidence_score=v_data['confidence_score'],
                resolved_by=v_data.get('resolved_by')
            )
        else:
            vio.status = v_data['status']
            vio.save()

        # Seed linked notification
        Notification.objects.get_or_create(
            violation=vio,
            defaults={
                'message': f"Safety Alert: {vio.violation_type} detected on {vio.source_file} (Severity: {vio.severity})",
                'is_read': vio.status == 'Resolved'
            }
        )

    print("[Seed] Seeded 12 comprehensive violation records & notifications into MySQL.")

    # 6. Seed Media Library Records (MediaFile)
    media_entries = [
        {'file_name': 'construction_1.mp4', 'file_type': 'video', 'file_path': 'videos/construction_1.mp4'},
        {'file_name': 'construction_2.mp4', 'file_type': 'video', 'file_path': 'videos/construction_2.mp4'},
        {'file_name': 'helmet_violation.mp4', 'file_type': 'video', 'file_path': 'videos/helmet_violation.mp4'},
        {'file_name': 'fire_alert.mp4', 'file_type': 'video', 'file_path': 'videos/fire_alert.mp4'},
        {'file_name': 'worker_with_helmet.jpg', 'file_type': 'image', 'file_path': 'images/worker_with_helmet.jpg'},
        {'file_name': 'worker_without_helmet.jpg', 'file_type': 'image', 'file_path': 'images/worker_without_helmet.jpg'},
        {'file_name': 'worker_without_vest.jpg', 'file_type': 'image', 'file_path': 'images/worker_without_vest.jpg'},
        {'file_name': 'fire.jpg', 'file_type': 'image', 'file_path': 'images/fire.jpg'},
    ]

    for m in media_entries:
        MediaFile.objects.get_or_create(
            file_name=m['file_name'],
            defaults={
                'file_type': m['file_type'],
                'file_path': m['file_path'],
                'detection_summary': {'status': 'Analyzed by YOLOv8 Safety Pipeline'}
            }
        )

    print("[Seed] Seeded Media Library records into database.")

    # 7. Generate & Seed Compliance Reports (SystemReport)
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    report_configs = [
        {
            'report_type': 'daily_attendance',
            'file_format': 'csv',
            'filename': 'report_daily_attendance_20260909.csv',
            'headers': ['Worker ID', 'Name', 'Department', 'Date', 'Entry Time', 'Exit Time', 'Working Hours', 'Status'],
            'rows': [
                ['W-001', 'Pavan Sai', 'Safety', str(today), '08:00:00', '16:15:00', '8.25', 'Completed'],
                ['W-002', 'Rajesh Kumar', 'Civil', str(today), '08:15:00', '16:30:00', '8.25', 'Completed'],
                ['W-003', 'Vikram Singh', 'Mechanical', str(today), '08:05:00', '16:00:00', '7.92', 'Completed'],
                ['W-004', 'Priya Sharma', 'Electrical', str(today), '08:00:00', 'In Shift', '4.50', 'Present'],
                ['W-005', 'Amit Patel', 'Civil', str(today), '08:30:00', 'In Shift', '4.00', 'Present'],
                ['W-006', 'Suresh Reddy', 'Mechanical', str(today), '08:45:00', 'In Shift', '3.75', 'Present'],
                ['W-007', 'Sunita Verma', 'Safety', str(today), '08:00:00', '16:00:00', '8.00', 'Completed'],
                ['W-008', 'Rahul Gupta', 'Civil', str(today), '08:10:00', '16:10:00', '8.00', 'Completed'],
            ]
        },
        {
            'report_type': 'weekly_summary',
            'file_format': 'csv',
            'filename': 'report_weekly_summary_20260909.csv',
            'headers': ['Category', 'Compliant Inspections', 'Violations Detected', 'Resolved Count', 'Compliance Rate (%)'],
            'rows': [
                ['Safety Helmet Detection', '142', '4', '3', '97.2%'],
                ['High-Vis Vest Detection', '135', '3', '2', '97.8%'],
                ['Gloves & Boots Compliance', '128', '3', '2', '97.7%'],
                ['Fire & Smoke Alarm', '48', '2', '1', '95.8%'],
                ['Restricted Area Access', '96', '2', '1', '97.9%'],
                ['Overall Site PPE Audit', '549', '14', '9', '97.4%']
            ]
        },
        {
            'report_type': 'monthly_compliance',
            'file_format': 'csv',
            'filename': 'report_monthly_compliance_20260909.csv',
            'headers': ['Site Zone', 'Supervising Engineer', 'Active Workers', 'Safety Score (100)', 'Audit Status'],
            'rows': [
                ['Zone A Main Construction', 'Pavan Sai', '14', '95', 'Passed Audit'],
                ['Zone B Machinery & Crane', 'Rajesh Kumar', '12', '92', 'Passed Audit'],
                ['Zone C Electrical Rigging', 'Priya Sharma', '8', '98', 'Passed Audit'],
                ['Zone D Excavation Vault', 'Sunita Verma', '10', '90', 'Passed Audit'],
            ]
        },
        {
            'report_type': 'worker_activity',
            'file_format': 'csv',
            'filename': 'report_worker_activity_20260909.csv',
            'headers': ['Worker ID', 'Name', 'Total Shifts', 'Total Hours Logged', 'Violations Flagged', 'Safety Score'],
            'rows': [
                ['W-001', 'Pavan Sai', '22', '176.5', '0', '95'],
                ['W-002', 'Rajesh Kumar', '21', '168.0', '1', '88'],
                ['W-003', 'Vikram Singh', '20', '160.0', '1', '92'],
                ['W-004', 'Priya Sharma', '23', '184.0', '1', '100'],
                ['W-005', 'Amit Patel', '18', '144.0', '2', '78'],
                ['W-006', 'Suresh Reddy', '19', '152.0', '2', '85'],
                ['W-007', 'Sunita Verma', '22', '176.0', '0', '98'],
                ['W-008', 'Rahul Gupta', '21', '168.0', '1', '90'],
            ]
        },
        {
            'report_type': 'violations_export',
            'file_format': 'csv',
            'filename': 'report_violations_export_20260909.csv',
            'headers': ['Violation ID', 'Worker Name', 'Type', 'Severity', 'Source File', 'Status', 'Confidence Score'],
            'rows': [
                ['ALT-1001', 'Amit Patel', 'Helmet Missing', 'High', 'construction_1.mp4', 'Pending', '96.5%'],
                ['ALT-1002', 'Suresh Reddy', 'Safety Vest Missing', 'Medium', 'helmet_violation.mp4', 'Resolved', '91.2%'],
                ['ALT-1003', 'Unidentified', 'Fire Hazard', 'Critical', 'fire_alert.mp4', 'Pending', '99.1%'],
                ['ALT-1004', 'Vikram Singh', 'Gloves Missing', 'Low', 'construction_2.mp4', 'Resolved', '88.4%'],
                ['ALT-1005', 'Rajesh Kumar', 'Boots Missing', 'Low', 'construction_1.mp4', 'Resolved', '89.0%'],
                ['ALT-1006', 'Rahul Gupta', 'Restricted Area', 'High', 'Zone C Gate Kiosk', 'Pending', '94.8%'],
                ['ALT-1007', 'Security Intruder', 'Unrecognized Intruder', 'High', 'Main Gate Kiosk', 'Pending', '34.2%'],
                ['ALT-1008', 'Suresh Reddy', 'Helmet Missing', 'High', 'construction_2.mp4', 'Pending', '97.0%'],
                ['ALT-1009', 'Amit Patel', 'Safety Vest Missing', 'Medium', 'construction_1.mp4', 'Resolved', '93.5%'],
                ['ALT-1010', 'Unidentified', 'Fire Hazard', 'Critical', 'fire.jpg', 'Resolved', '98.7%'],
                ['ALT-1011', 'Priya Sharma', 'Gloves Missing', 'Low', 'Zone B Wiring', 'Pending', '90.5%'],
                ['ALT-1012', 'Unidentified', 'Unrecognized Intruder', 'High', 'Gate Kiosk 2', 'Pending', '41.0%'],
            ]
        }
    ]

    for rc in report_configs:
        file_p = os.path.join(reports_dir, rc['filename'])
        with open(file_p, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(rc['headers'])
            writer.writerows(rc['rows'])

        rel_path = f"{settings.MEDIA_URL}reports/{rc['filename']}"
        SystemReport.objects.get_or_create(
            report_type=rc['report_type'],
            file_format=rc['file_format'],
            defaults={
                'file_path': rel_path,
                'record_count': len(rc['rows'])
            }
        )

    print("[Seed] Created all compliance audit reports & CSV files in media/reports/.")
    print("[Seed] Complete database seeding finished successfully!")

if __name__ == '__main__':
    seed()
