import os

try:
    from celery import Celery
except ImportError:
    Celery = None

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safevision.settings')

app = None
if Celery is not None:
    app = Celery('safevision')
    app.config_from_object('django.conf:settings', namespace='CELERY')
    app.autodiscover_tasks()
