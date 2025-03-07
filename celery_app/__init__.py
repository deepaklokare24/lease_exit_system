from celery import Celery
from config.config import config

# Get Redis URL from config
redis_url = config.get_env("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
app = Celery('lease_exit_system',
             broker=redis_url,
             backend=redis_url,
             include=['celery_app.tasks'])  # Include tasks module

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30,
    result_expires=3600,
    broker_connection_retry_on_startup=True
) 