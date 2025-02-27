import os
import logging
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from config.config import load_config
from api.routes import workflow, form, approval, notification
from database.connection import init_database, close_database
from utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Create startup and shutdown event handlers
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load config and initialize database
    logger.info("Starting Lease Exit System server")
    config = load_config()
    
    try:
        logger.info("Initializing database connection")
        await init_database(config["database"])
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    yield
    
    # Shutdown: Close database connection
    logger.info("Shutting down Lease Exit System server")
    try:
        logger.info("Closing database connection")
        await close_database()
    except Exception as e:
        logger.error(f"Error during database shutdown: {str(e)}")

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
app.include_router(form.router, prefix="/api/forms", tags=["Forms"])
app.include_router(approval.router, prefix="/api/approvals", tags=["Approvals"])
app.include_router(notification.router, prefix="/api/notifications", tags=["Notifications"])

# Mount static files for frontend (for production)
static_dir = os.path.join(os.path.dirname(__file__), "frontend/build")
if os.path.exists(static_dir):
    logger.info(f"Mounting static files from {static_dir}")
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
