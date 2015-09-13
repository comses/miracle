from __future__ import absolute_import

from django.conf import settings
from celery import Celery

app = Celery('miracle',
             broker=settings.CELERY_BROKER_URL,
             backend=settings.CELERY_BACKEND,
             include=['miracle.tasks'])

app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    app.start()
