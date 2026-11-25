from django.db import models
from django.contrib.auth.models import User
import uuid

class Worker(models.Model):
    ROLE_CHOICES = [
        ('Laborer', 'Site Laborer'),
        ('Supervisor', 'Site Supervisor'),
        ('Engineer', 'Safety Engineer'),
        ('Electrician', 'Electrician'),
        ('Operator', 'Equipment Operator'),
    ]

    DEPARTMENT_CHOICES = [
        ('Civil', 'Civil Construction'),
        ('Electrical', 'Electrical & Wiring'),
        ('Mechanical', 'Heavy Machinery'),
        ('Safety', 'Safety & Compliance'),
    ]

    worker_id = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Laborer')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='Civil')
    photo = models.ImageField(upload_to='worker_photos/', null=True, blank=True)
    joining_date = models.DateField()
    face_encoding = models.JSONField(null=True, blank=True, help_text="ArcFace 512d or 128d facial feature vector")
    safety_score = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.worker_id} - {self.full_name}"

class WorkerFace(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='registered_faces')
    photo = models.ImageField(upload_to='faces/')
    embedding_vector = models.JSONField(null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Face template for {self.worker.full_name}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Late', 'Late'),
        ('Left Early', 'Left Early'),
        ('Completed', 'Shift Completed'),
    ]

    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(auto_now_add=True)
    entry_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')
    total_hours = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-date', '-entry_time']

    def __str__(self):
        return f"Attendance {self.worker.worker_id} - {self.date}"

class Shift(models.Model):
    SHIFT_TYPES = [
        ('Morning', 'Morning Shift (08:00 - 16:00)'),
        ('Evening', 'Evening Shift (16:00 - 00:00)'),
        ('Night', 'Night Shift (00:00 - 08:00)'),
    ]

    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='shifts')
    date = models.DateField()
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPES, default='Morning')
    status = models.CharField(max_length=20, default='Scheduled')

    def __str__(self):
        return f"{self.shift_type} Shift - {self.worker.full_name}"

class Violation(models.Model):
    SEVERITY_CHOICES = [
        ('Low', 'Low Risk'),
        ('Medium', 'Medium Hazard'),
        ('High', 'High Severity'),
        ('Critical', 'Critical Danger'),
    ]

    VIOLATION_TYPES = [
        ('Helmet Missing', 'Helmet Missing'),
        ('Safety Vest Missing', 'Safety Vest Missing'),
        ('Gloves Missing', 'Gloves Missing'),
        ('Boots Missing', 'Boots Missing'),
        ('Fire Hazard', 'Fire / Smoke Hazard'),
        ('Restricted Area', 'Restricted Area Violation'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending Resolution'),
        ('Resolved', 'Resolved'),
    ]

    violation_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='violations')
    violation_type = models.CharField(max_length=50, choices=VIOLATION_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='High')
    source_file = models.CharField(max_length=255, default='Live Camera')
    source_type = models.CharField(max_length=50, default='Pre-built Video')
    timestamp = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(default=0.0)
    confidence_score = models.FloatField(default=95.0)
    tracking_id = models.CharField(max_length=50, null=True, blank=True)
    snapshot = models.ImageField(upload_to='violations/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.violation_id} - {self.violation_type} ({self.severity})"

class AISystemConfig(models.Model):
    processing_fps = models.IntegerField(default=10)
    confidence_threshold = models.FloatField(default=0.50)
    frame_skip = models.IntegerField(default=2)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI Config (FPS: {self.processing_fps}, Conf: {self.confidence_threshold}, Skip: {self.frame_skip})"

class MediaFile(models.Model):
    FILE_TYPES = [
        ('video', 'Video Stream'),
        ('image', 'Static Image'),
    ]

    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_path = models.FileField(upload_to='media_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    output_path = models.CharField(max_length=255, null=True, blank=True)
    detection_summary = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.file_name} ({self.file_type})"

class Notification(models.Model):
    violation = models.ForeignKey(Violation, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class SystemReport(models.Model):
    REPORT_TYPES = [
        ('daily_attendance', 'Daily Attendance Report'),
        ('weekly_summary', 'Weekly Safety Report'),
        ('monthly_compliance', 'Monthly Compliance Report'),
        ('worker_activity', 'Worker Activity Log'),
        ('violations_export', 'Violation Export Report'),
    ]

    FORMAT_CHOICES = [
        ('pdf', 'PDF Document'),
        ('csv', 'CSV Table'),
        ('xlsx', 'Excel Spreadsheet'),
    ]

    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    file_format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    generated_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=255)
    record_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Report {self.report_type} ({self.file_format})"
