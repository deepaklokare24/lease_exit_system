from utils.test_connections import test_smtp_connection, test_llm_connection, test_mongodb_connection  
from utils.test_tasks import test_task_queue
import asyncio

# Test database connection
asyncio.run(test_mongodb_connection())

# Test email
#test_smtp_connection()

# Test LLM
#test_llm_connection()

# Test task queue
#test_task_queue()