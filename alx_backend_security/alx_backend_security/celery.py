import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_security.settings')

app = Celery('alx_backend_security', broker='redis://localhost:6379/0')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()