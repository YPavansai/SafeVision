from django.contrib import admin
from .models import Worker, WorkerFace, Attendance, Shift, Violation, MediaFile, Notification, SystemReport

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('worker_id', 'full_name', 'role', 'department', 'safety_score', 'is_active', 'joining_date')
    search_fields = ('worker_id', 'full_name', 'phone_number')
    list_filter = ('role', 'department', 'is_active')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('worker', 'date', 'entry_time', 'exit_time', 'total_hours', 'status')
    list_filter = ('status', 'date')

@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ('violation_id', 'worker', 'violation_type', 'severity', 'source_file', 'status', 'timestamp')
    list_filter = ('severity', 'status', 'violation_type')

admin.site.register(WorkerFace)
admin.site.register(Shift)
admin.site.register(MediaFile)
admin.site.register(Notification)
admin.site.register(SystemReport)
