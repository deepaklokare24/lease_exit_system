"""
Celery application configuration.

This file defines the Celery application instance used for task processing.
"""

import os
import sys
from celery import Celery
from config.config import config

# Add the project root directory to Python path to ensure modules can be found
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Set default environment variables
os.environ.setdefault('CELERY_BROKER_URL', config.get_redis_url())
os.environ.setdefault('CELERY_RESULT_BACKEND', config.get_redis_url())

# Create Celery app
celery_app = Celery('lease_exit_system')

# Load configuration from environment variables with prefix 'CELERY_'
celery_app.config_from_envvar('CELERY_CONFIG_MODULE', silent=True)
celery_app.conf.update(
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_hijack_root_logger=False,
    worker_redirect_stdouts=False,
    include=[
        'celery_tasks'
    ]
)

# Auto-discover tasks from all registered app modules
# Using include instead of autodiscover_tasks to avoid import issues
# celery_app.autodiscover_tasks([
#     'tasks.notification_tasks', 
#     'tasks.approval_tasks', 
#     'tasks.form_tasks', 
#     'tasks.workflow_tasks'
# ])

# Define what happens when worker starts
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Import tasks here to avoid circular imports
    # We'll use a try/except block to handle potential import errors
    try:
        # Import the periodic tasks
        from celery_tasks import (
            check_pending_approvals,
            check_workflow_deadlines,
            resend_failed_notifications
        )
        
        # Schedule periodic tasks
        sender.add_periodic_task(
            3600.0,  # 1 hour
            check_pending_approvals.s(),
            name='check-pending-approvals-hourly'
        )
        
        sender.add_periodic_task(
            3600.0,  # 1 hour
            check_workflow_deadlines.s(),
            name='check-workflow-deadlines-hourly'
        )
        
        sender.add_periodic_task(
            86400.0,  # 24 hours
            resend_failed_notifications.s(),
            name='resend-failed-notifications-daily'
        )
    except ImportError as e:
        print(f"Warning: Could not import periodic tasks: {e}")
        # Continue without setting up periodic tasks

if __name__ == '__main__':
    celery_app.start() 