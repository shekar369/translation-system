from celery import Celery
import os
from decouple import config

# Get configuration from environment
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    "translation_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.workers.translation_worker']
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

if __name__ == '__main__':
    celery_app.start()
