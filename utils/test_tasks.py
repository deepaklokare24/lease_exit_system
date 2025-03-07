import logging
from datetime import datetime
import time
import redis
from config.config import config
from celery_app import app as celery_app
from celery_app.tasks import test_background_task

logger = logging.getLogger(__name__)

def test_task_queue():
    """Test task queue functionality"""
    try:
        # Initialize Redis client
        redis_url = config.get_env("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url)
        
        # Clear test queue
        redis_client.delete('test_queue')
        
        # Submit test tasks
        tasks = []
        for i in range(3):
            task_id = f"test_task_{i}"
            task = test_background_task.delay(task_id)
            tasks.append((task_id, task))
            logger.info(f"Submitted task {task_id}")
        
        # Wait for tasks to complete
        results = []
        for task_id, task in tasks:
            try:
                result = task.get(timeout=10)  # Wait up to 10 seconds
                if isinstance(result, dict) and result.get("status") == "completed":
                    results.append((task_id, "success", result))
                    logger.info(f"Task {task_id} completed successfully")
                else:
                    results.append((task_id, "failed", "Invalid result format"))
                    logger.error(f"Task {task_id} returned invalid result: {result}")
            except Exception as e:
                results.append((task_id, "failed", str(e)))
                logger.error(f"Task {task_id} failed: {str(e)}")
        
        # Verify results
        success = all(r[1] == "success" for r in results)
        if success:
            logger.info("✓ Task queue test successful")
        else:
            failed = [r[0] for r in results if r[1] == "failed"]
            logger.error(f"✗ Task queue test failed. Failed tasks: {', '.join(failed)}")
        
        return {
            "success": success,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"✗ Task queue test failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def test_queue_performance():
    """Test queue performance and capacity"""
    try:
        start_time = time.time()
        tasks = []
        
        # Submit 10 tasks in rapid succession
        for i in range(10):
            task_id = f"perf_test_{i}"
            task = test_background_task.delay(task_id)
            tasks.append((task_id, task))
        
        # Wait for all tasks to complete
        completed = 0
        failed = 0
        for task_id, task in tasks:
            try:
                result = task.get(timeout=30)  # Wait up to 30 seconds
                if isinstance(result, dict) and result.get("status") == "completed":
                    completed += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        performance = {
            "total_tasks": len(tasks),
            "completed": completed,
            "failed": failed,
            "duration_seconds": duration,
            "tasks_per_second": completed / duration if duration > 0 else 0
        }
        
        logger.info(f"Queue performance test results: {performance}")
        return performance
        
    except Exception as e:
        logger.error(f"Queue performance test failed: {str(e)}")
        return None

def verify_task_system():
    """Verify task system is working correctly"""
    try:
        results = {
            "queue_test": False,
            "performance_test": False
        }
        
        # Test basic task queue functionality
        try:
            queue_test = test_task_queue()
            if queue_test["success"]:
                logger.info("✓ Task queue test passed")
                results["queue_test"] = True
            else:
                logger.warning("Task queue test failed, but continuing")
        except Exception as e:
            logger.error(f"Task queue test error: {str(e)}")
        
        # Test queue performance
        try:
            perf_test = test_queue_performance()
            if perf_test and perf_test["failed"] == 0:
                logger.info("✓ Queue performance test passed")
                results["performance_test"] = True
            else:
                logger.warning("Queue performance test showed some failures, but continuing")
        except Exception as e:
            logger.error(f"Queue performance test error: {str(e)}")
        
        # Consider the system verified if at least the basic queue test passed
        system_ok = results["queue_test"]
        
        if system_ok:
            logger.info("✓ Task system verification completed successfully")
        else:
            logger.warning("Task system verification completed with warnings")
            
        return system_ok
        
    except Exception as e:
        logger.error(f"Task system verification failed: {str(e)}")
        return False 