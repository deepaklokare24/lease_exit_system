import os
import logging
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Define log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Environment-based configuration
ENV = os.getenv("ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if ENV == "development" else "INFO")

# Configure console and file handlers
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, f"lease_exit_system.log"),
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

# Configure error log handler
error_file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, f"lease_exit_system_error.log"),
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
error_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
error_file_handler.setLevel(logging.ERROR)

def setup_logger(name):
    """
    Configure and return a logger with the given name.
    
    Args:
        name: The name of the logger
        
    Returns:
        A configured logger
    """
    logger = logging.getLogger(name)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Set log level based on environment
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)
    
    # Don't propagate to root logger
    logger.propagate = False
    
    return logger

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the log record.
    """
    def __init__(self, **kwargs):
        self.json_default = kwargs.pop("json_default", str)
        self.json_encoder = kwargs.pop("json_encoder", None)
        super(JsonFormatter, self).__init__()

    def format(self, record):
        log_record = {}
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["name"] = record.name
        log_record["message"] = record.getMessage()
        
        if hasattr(record, "props"):
            log_record["props"] = record.props

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, default=self.json_default, cls=self.json_encoder)

def get_json_logger(name):
    """
    Get a logger that outputs logs as JSON - useful for structured logging systems.
    
    Args:
        name: The name of the logger
        
    Returns:
        A configured logger with JSON formatting
    """
    logger = logging.getLogger(f"{name}_json")
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Set log level based on environment
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Create JSON handlers
    json_console_handler = logging.StreamHandler()
    json_console_handler.setFormatter(JsonFormatter())
    
    json_file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, f"lease_exit_system_json.log"),
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    json_file_handler.setFormatter(JsonFormatter())
    
    # Add handlers
    logger.addHandler(json_console_handler)
    logger.addHandler(json_file_handler)
    
    # Don't propagate to root logger
    logger.propagate = False
    
    return logger

def log_with_context(logger, level, message, **context):
    """
    Log a message with additional context data.
    
    Args:
        logger: The logger to use
        level: The log level (e.g., "info", "error")
        message: The log message
        **context: Additional context as keyword arguments
    """
    log_method = getattr(logger, level.lower())
    
    if getattr(logger, 'handlers', None) and isinstance(logger.handlers[0].formatter, JsonFormatter):
        # For JSON loggers, add context to the record
        log_method(message, extra={"props": context})
    else:
        # For regular loggers, append context as a string
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            log_method(f"{message} - {context_str}")
        else:
            log_method(message) 