import hashlib
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

logger = logging.getLogger('safevision.ai')

MAX_ACTIVE_JOBS = int(os.environ.get('MAX_ACTIVE_ANALYSIS_JOBS', 20))
_EXECUTOR_LOCK = threading.Lock()
_EXECUTOR = ThreadPoolExecutor(max_workers=int(os.environ.get('AI_JOB_WORKERS', 2)))


def compute_file_sha256(filepath):
    """Computes SHA-256 hash in chunks to avoid loading large files into RAM."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def run_image_analysis_job(job_pk, processor):
    """Executes an AnalysisJob synchronously in a worker thread or Celery worker."""
    from api.models import AnalysisJob

    close_old_connections()
    start = time.perf_counter()
    try:
        job = AnalysisJob.objects.select_related('media_file').get(pk=job_pk)
        job.status = 'Processing'
        job.error_message = ''
        job.save(update_fields=['status', 'error_message', 'updated_at'])

        res = processor.process_image(job.input_path)
        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)

        public_result = {
            'detections': res.get('detections', []),
            'violations': res.get('violations', []),
            'workers_analysis': res.get('workers_analysis', []),
            'safety_score': res.get('safety_score', 100),
            'output_url': res.get('output_url'),
            'total_objects': res.get('total_objects', 0),
            'model_capabilities': res.get('model_capabilities', {}),
            'processing_time_ms': duration_ms,
        }

        if job.media_file:
            job.media_file.output_path = res.get('output_url')
            job.media_file.detection_summary = {
                'total_objects': res.get('total_objects', 0),
                'safety_score': res.get('safety_score', 100),
                'violations_count': len(res.get('violations', [])),
            }
            job.media_file.save(update_fields=['output_path', 'detection_summary'])

        job.status = 'Completed'
        job.result = public_result
        job.processing_time_ms = duration_ms
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'result', 'processing_time_ms', 'completed_at', 'updated_at'])
        logger.info("analysis_job_completed job_id=%s duration_ms=%s", job.job_id, duration_ms)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
        logger.error("analysis_job_failed job_pk=%s error=%s", job_pk, exc)
        try:
            job = AnalysisJob.objects.get(pk=job_pk)
            job.status = 'Failed'
            job.error_message = str(exc)
            job.processing_time_ms = duration_ms
            job.save(update_fields=['status', 'error_message', 'processing_time_ms', 'updated_at'])
        except Exception:
            pass
    finally:
        close_old_connections()


def enqueue_image_analysis_job(job, processor):
    """
    Dispatches an AnalysisJob to Celery (if enabled & available) or bounded ThreadPoolExecutor.
    Enforces MAX_ACTIVE_JOBS queue limit.
    """
    from api.models import AnalysisJob

    active_count = AnalysisJob.objects.filter(status__in=['Pending', 'Processing']).exclude(pk=job.pk).count()
    if active_count >= MAX_ACTIVE_JOBS:
        job.status = 'Failed'
        job.error_message = 'Analysis queue is full. Please retry shortly.'
        job.save(update_fields=['status', 'error_message', 'updated_at'])
        raise RuntimeError(job.error_message)

    if getattr(settings, 'USE_CELERY', False) and getattr(settings, 'CELERY_BROKER_URL', ''):
        try:
            from api.tasks import execute_analysis_job_task
            execute_analysis_job_task.delay(job.pk)
            return 'celery'
        except Exception as exc:
            logger.warning("Celery dispatch failed (%s); falling back to bounded local pool.", exc)

    _EXECUTOR.submit(run_image_analysis_job, job.pk, processor)
    return 'local_pool'


def get_worker_backend_status():
    """Reports background worker status for /api/health/."""
    if getattr(settings, 'USE_CELERY', False) and getattr(settings, 'CELERY_BROKER_URL', ''):
        return {'mode': 'celery', 'status': 'CONFIGURED', 'max_active_jobs': MAX_ACTIVE_JOBS}
    return {
        'mode': 'local_thread_pool',
        'status': 'ONLINE',
        'max_workers': _EXECUTOR._max_workers,
        'max_active_jobs': MAX_ACTIVE_JOBS,
    }
