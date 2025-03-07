import logging
import redis
from celery import Celery
from motor.motor_asyncio import AsyncIOMotorClient
from anthropic import Anthropic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.config import config
import asyncio

logger = logging.getLogger(__name__)

async def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        client = AsyncIOMotorClient(config.get_env("MONGODB_URI"))
        await client.admin.command('ping')
        logger.info("✓ MongoDB connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ MongoDB connection failed: {str(e)}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    try:
        redis_url = config.get_env("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url)
        redis_client.ping()
        logger.info("✓ Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {str(e)}")
        return False

def test_celery_connection():
    """Test Celery worker connection"""
    try:
        app = Celery('lease_exit_system',
                    broker=config.get_env("REDIS_URL", "redis://localhost:6379/0"))
        
        # Try to ping workers
        i = app.control.inspect()
        if not i.ping():
            raise Exception("No running Celery workers found")
        
        logger.info("✓ Celery workers are running")
        return True
    except Exception as e:
        logger.error(f"✗ Celery connection failed: {str(e)}")
        return False

def test_smtp_connection():
    """Test SMTP connection and send test email"""
    try:
        smtp_host = config.get_env("SMTP_HOST")
        smtp_port = int(config.get_env("SMTP_PORT"))
        smtp_username = config.get_env("SMTP_USERNAME")
        smtp_password = config.get_env("SMTP_PASSWORD")
        from_email = config.get_env("FROM_EMAIL")

        # Create test message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = smtp_username  # Send to self for testing
        msg['Subject'] = "Lease Exit System - Test Email"
        body = "This is a test email from the Lease Exit System. If you receive this, email notifications are working correctly."
        msg.attach(MIMEText(body, 'plain'))

        # Connect and send
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()

        logger.info("✓ SMTP connection and test email successful")
        return True
    except Exception as e:
        logger.error(f"✗ SMTP connection failed: {str(e)}")
        return False

def test_llm_connection():
    """Test Anthropic API connection"""
    try:
        api_key = config.get_env("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("✗ Anthropic API key not found in environment variables")
            return False

        anthropic = Anthropic(api_key=api_key)
        logger.info("Attempting to connect to Anthropic API...")
        
        try:
            # Create a simple message to test the connection
            response = anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{
                    "role": "user",
                    "content": "Say 'Connection successful' if you can read this."
                }]
            )
            
            # Log the response for debugging
            logger.debug(f"Full API Response: {response}")
            
            # Extract the response content
            # In Claude 3, response.content is a list of Content objects
            if hasattr(response, 'content'):
                # Get the text from the first content block
                text_blocks = [
                    block.text for block in response.content 
                    if hasattr(block, 'text')
                ]
                
                # Combine all text blocks
                full_response = " ".join(text_blocks)
                logger.info(f"Received response: {full_response}")
                
                # Check if our expected text is in any of the text blocks
                if any("Connection successful" in block for block in text_blocks):
                    logger.info("✓ Anthropic API connection successful")
                    return True
                else:
                    logger.error(f"✗ Expected response not found in content: {text_blocks}")
                    return False
            else:
                logger.error("✗ Response missing content attribute")
                logger.debug(f"Response structure: {dir(response)}")
                return False
                
        except Exception as api_error:
            logger.error(f"✗ API call failed: {str(api_error)}")
            if hasattr(api_error, 'response'):
                logger.error(f"API Error Response: {api_error.response}")
            if hasattr(api_error, 'status_code'):
                logger.error(f"Status Code: {api_error.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Anthropic API connection failed: {str(e)}")
        logger.debug("Error details:", exc_info=True)
        return False

async def test_all_connections():
    """Test all system connections"""
    results = {
        "mongodb": await test_mongodb_connection(),
        "redis": test_redis_connection(),
        "celery": test_celery_connection(),
        "smtp": test_smtp_connection(),
        "llm": test_llm_connection()
    }
    
    all_passed = all(results.values())
    if all_passed:
        logger.info("✓ All system connections are working correctly")
    else:
        failed = [k for k, v in results.items() if not v]
        logger.error(f"✗ Some connections failed: {', '.join(failed)}")
    
    return results

async def verify_system_health():
    """Verify all system components are healthy before starting the application"""
    try:
        # Run all connection tests
        results = await test_all_connections()
        
        # Check if any critical components failed
        critical_components = ["mongodb", "redis", "celery", "llm"]
        critical_failures = [k for k in critical_components if not results.get(k)]
        
        if critical_failures:
            raise SystemError(f"Critical system components failed: {', '.join(critical_failures)}")
        
        # Log warnings for non-critical failures
        non_critical = [k for k, v in results.items() if not v and k not in critical_components]
        if non_critical:
            logger.warning(f"Non-critical components failed: {', '.join(non_critical)}")
        
        return True
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return False 