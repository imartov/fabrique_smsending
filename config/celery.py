from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
# app.conf.task_acks_late = True
# app.conf.worker_prefetch_multiplier = 1
app.control.purge() # delete all tasks

app.conf.beat_schedule = {
    'send_stat': {
        'task': 'smsending.tasks.send_stat',
        'schedule': crontab(minute=0, hour=7),
    },
}