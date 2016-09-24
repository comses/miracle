from __future__ import absolute_import

from django.conf import settings
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miracle.settings')

app = Celery('miracle',
             backend=settings.CELERY_RESULT_BACKEND)

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
