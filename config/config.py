import os
import yaml
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """Configuration management for the application"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration"""
        if self._initialized:
            return
        
        self.config_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.config_dir)
        
        # Load configuration files
        self.agents_config = self._load_config("agents.yaml")
        self.workflows_config = self._load_config("workflows.yaml")
        self.tasks_config = self._load_config("tasks.yaml")
        
        # Set initialized flag
        self._initialized = True
    
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """Load a YAML configuration file
        
        Args:
            filename: The name of the configuration file
            
        Returns:
            The configuration data
        """
        config_path = os.path.join(self.config_dir, filename)
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                logger.info(f"Loaded configuration from {config_path}")
                return config or {}
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {str(e)}")
            return {}
    
    def get_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """Get the configuration for an agent
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            The agent configuration
        """
        return self.agents_config.get(agent_id, {})
    
    def get_workflow_config(self, workflow_id: str) -> Dict[str, Any]:
        """Get the configuration for a workflow
        
        Args:
            workflow_id: The ID of the workflow
            
        Returns:
            The workflow configuration
        """
        return self.workflows_config.get(workflow_id, {})
    
    def get_task_config(self, task_category: str, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the configuration for a task
        
        Args:
            task_category: The category of the task
            task_id: The ID of the task
            
        Returns:
            The task configuration
        """
        tasks = self.tasks_config.get(task_category, [])
        for task in tasks:
            if task.get("id") == task_id:
                return task
        return None
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """Get an environment variable
        
        Args:
            key: The name of the environment variable
            default: Default value if not found
            
        Returns:
            The value of the environment variable
        """
        return os.getenv(key, default)
    
    def get_mongodb_uri(self) -> str:
        """Get the MongoDB URI
        
        Returns:
            The MongoDB URI
        """
        return self.get_env("MONGODB_URI", "mongodb://localhost:27017/lease_exit_system")
    
    def get_openai_config(self) -> Dict[str, str]:
        """Get the OpenAI configuration
        
        Returns:
            The OpenAI configuration
        """
        return {
            "api_key": self.get_env("OPENAI_API_KEY"),
            "model": self.get_env("AI_MODEL", "gpt-4o")
        }
        
    def get_anthropic_config(self) -> Dict[str, str]:
        """Get the Anthropic configuration
        
        Returns:
            The Anthropic configuration
        """
        return {
            "api_key": self.get_env("ANTHROPIC_API_KEY"),
            "model": self.get_env("AI_MODEL", "claude-3-sonnet-20240229")
        }
    
    def get_smtp_config(self) -> Dict[str, Any]:
        """Get the SMTP configuration
        
        Returns:
            The SMTP configuration
        """
        return {
            "host": self.get_env("SMTP_HOST"),
            "port": int(self.get_env("SMTP_PORT", "587")),
            "username": self.get_env("SMTP_USERNAME"),
            "password": self.get_env("SMTP_PASSWORD"),
            "from_email": self.get_env("FROM_EMAIL")
        }
    
    def get_upload_dir(self) -> str:
        """Get the upload directory
        
        Returns:
            The upload directory
        """
        upload_dir = self.get_env("UPLOAD_DIR", "uploads")
        if not os.path.isabs(upload_dir):
            upload_dir = os.path.join(self.base_dir, upload_dir)
        
        # Create the directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        return upload_dir
    
    def is_development(self) -> bool:
        """Check if the application is in development mode
        
        Returns:
            Whether the application is in development mode
        """
        return self.get_env("APP_ENV", "development").lower() == "development"
    
    def is_testing(self) -> bool:
        """Check if the application is in testing mode
        
        Returns:
            Whether the application is in testing mode
        """
        return self.get_env("APP_ENV", "development").lower() == "testing"
    
    def is_production(self) -> bool:
        """Check if the application is in production mode
        
        Returns:
            Whether the application is in production mode
        """
        return self.get_env("APP_ENV", "development").lower() == "production"


# Create a singleton instance
config = Config()
