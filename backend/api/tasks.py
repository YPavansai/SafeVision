try:
    from celery import shared_task
except ImportError:
    def shared_task(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def execute_analysis_job_task(self, job_pk):
    """Celery task wrapper for asynchronous YOLOv8 analysis."""
    from api.views import processor
    from api.job_runner import run_image_analysis_job

    run_image_analysis_job(job_pk, processor)
