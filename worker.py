"""
Celery worker entry point.

This file is used to start Celery workers and Flower monitoring.
Run with:
    celery -A worker worker --loglevel=info
    celery -A worker flower --port=5555
"""

from app import celery_app

# This import is needed to register all tasks with Celery
import tasks.notification_tasks
import tasks.approval_tasks
import tasks.form_tasks
import tasks.workflow_tasks

if __name__ == '__main__':
    celery_app.start() 