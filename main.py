import os
import logging
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from config.config import config
from api.routes import workflow, forms, notifications, approval
from database.connection import Database
from utils.logger import setup_logger
from utils.test_connections import verify_system_health
from utils.test_tasks import verify_task_system
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(process)d - %(name)s-%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create startup and shutdown event handlers
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load config and initialize database
    logger.info("Starting Lease Exit System server")
    
    try:
        await Database.connect()
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {str(e)}")
        raise
    
    # Perform system checks
    logger.info("Performing system health checks...")
    
    # Verify system connections with retries
    max_retries = 3
    retry_count = 0
    health_check_passed = False
    
    while retry_count < max_retries and not health_check_passed:
        try:
            health_check_passed = await verify_system_health()
            if not health_check_passed:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"System health check failed. Retrying ({retry_count}/{max_retries})...")
                    await asyncio.sleep(2)  # Wait 2 seconds before retrying
        except Exception as e:
            retry_count += 1
            logger.error(f"Error during health check: {str(e)}")
            if retry_count < max_retries:
                logger.warning(f"Retrying health check ({retry_count}/{max_retries})...")
                await asyncio.sleep(2)
    
    if not health_check_passed:
        logger.error("System health check failed after multiple retries.")
        # We'll continue anyway since we've made LLM non-critical
        logger.warning("Continuing startup despite health check failures. Some features may be limited.")
    else:
        logger.info("✓ System health check passed.")
    
    # Verify task system
    try:
        task_system_ok = verify_task_system()
        if not task_system_ok:
            logger.warning("Task system verification failed. Some workflow features may be limited.")
        else:
            logger.info("✓ Task system verification passed.")
    except Exception as e:
        logger.error(f"Error during task system verification: {str(e)}")
        logger.warning("Continuing startup despite task verification failure. Some features may be limited.")
    
    logger.info("✓ Application startup complete.")
    
    yield
    
    # Shutdown: Close database connection
    logger.info("Shutting down Lease Exit System server")
    try:
        await Database.disconnect()
        logger.info("Successfully disconnected from MongoDB")
    except Exception as e:
        logger.error(f"Error disconnecting from MongoDB: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="Lease Exit System API",
    description="API for the Lease Exit System powered by Crew AI Agents",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Include routers
app.include_router(workflow.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(forms.router, prefix="/api/forms", tags=["Forms"])
app.include_router(approval.router, prefix="/api/approvals", tags=["Approvals"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])

# Mount static files for frontend (for production)
static_dir = os.path.join(os.path.dirname(__file__), "frontend/build")
if os.path.exists(static_dir):
    logger.info(f"Mounting static files from {static_dir}")
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
