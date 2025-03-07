import logging
from datetime import datetime
import time
from celery_app import app

logger = logging.getLogger(__name__)

@app.task(name='test_task', bind=True)
def test_background_task(self, task_id: str):
    """Test background task execution"""
    try:
        logger.info(f"Executing test task {task_id}")
        time.sleep(2)  # Simulate some work
        return {
            "task_id": task_id,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        raise 