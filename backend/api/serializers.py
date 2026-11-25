from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Worker, WorkerFace, Attendance, Shift, Violation, MediaFile, Notification, SystemReport, AISystemConfig

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']

class WorkerFaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerFace
        fields = ['id', 'photo', 'registered_at']

class WorkerSerializer(serializers.ModelSerializer):
    registered_faces = WorkerFaceSerializer(many=True, read_only=True)

    class Meta:
        model = Worker
        fields = [
            'id', 'worker_id', 'full_name', 'phone_number', 'role',
            'department', 'photo', 'joining_date', 'face_encoding',
            'safety_score', 'is_active', 'created_at', 'registered_faces'
        ]

class AttendanceSerializer(serializers.ModelSerializer):
    worker_detail = WorkerSerializer(source='worker', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'worker', 'worker_detail', 'date', 'entry_time',
            'exit_time', 'status', 'total_hours'
        ]

class ShiftSerializer(serializers.ModelSerializer):
    worker_detail = WorkerSerializer(source='worker', read_only=True)

    class Meta:
        model = Shift
        fields = ['id', 'worker', 'worker_detail', 'date', 'shift_type', 'status']

class ViolationSerializer(serializers.ModelSerializer):
    worker_detail = WorkerSerializer(source='worker', read_only=True)

    class Meta:
        model = Violation
        fields = [
            'id', 'violation_id', 'worker', 'worker_detail', 'violation_type',
            'severity', 'source_file', 'source_type', 'timestamp', 'start_time',
            'end_time', 'duration_seconds', 'confidence_score', 'tracking_id',
            'snapshot', 'status', 'resolved_at', 'resolved_by'
        ]

class AISystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AISystemConfig
        fields = ['id', 'processing_fps', 'confidence_threshold', 'frame_skip', 'updated_at']

class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ['id', 'file_name', 'file_type', 'file_path', 'uploaded_at', 'output_path', 'detection_summary']

class NotificationSerializer(serializers.ModelSerializer):
    violation_detail = ViolationSerializer(source='violation', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'violation', 'violation_detail', 'message', 'is_read', 'created_at']

class SystemReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemReport
        fields = ['id', 'report_type', 'file_format', 'generated_at', 'file_path', 'record_count']
