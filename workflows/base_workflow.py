from typing import Dict, Any, List, Optional
from crewai import Flow
import os
import yaml
import logging
from abc import abstractmethod

logger = logging.getLogger(__name__)

class BaseWorkflow(Flow):
    """Base class for all workflows in the system"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the base workflow
        
        Args:
            config_path: Optional path to workflow configuration file
        """
        super().__init__()
        self.config = {}
        
        # Load configuration if provided
        if config_path:
            self.load_config(config_path)
        else:
            # Try to load from default location
            default_config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/workflows.yaml'
            )
            if os.path.exists(default_config_path):
                self.load_config(default_config_path)
                
        # Ensure subclasses implement required methods
        if not hasattr(self, 'setup_agents') or not callable(getattr(self, 'setup_agents')):
            raise NotImplementedError("Subclasses must implement setup_agents method")
        if not hasattr(self, 'setup_tools') or not callable(getattr(self, 'setup_tools')):
            raise NotImplementedError("Subclasses must implement setup_tools method")
    
    def load_config(self, config_path: str):
        """Load workflow configuration from a YAML file
        
        Args:
            config_path: Path to the configuration file
        """
        try:
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
                logger.info(f"Loaded workflow configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load workflow configuration: {str(e)}")
    
    def setup_agents(self):
        """Set up agents for the workflow
        
        This method should be implemented by subclasses to set up all required agents.
        """
        raise NotImplementedError("Subclasses must implement setup_agents method")
    
    def setup_tools(self):
        """Set up tools for the workflow
        
        This method should be implemented by subclasses to set up all required tools.
        """
        raise NotImplementedError("Subclasses must implement setup_tools method")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value
        
        Args:
            key: The configuration key
            default: Default value if key is not found
            
        Returns:
            The configuration value or default
        """
        return self.config.get(key, default)
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """Get the configuration for this workflow
        
        Returns:
            The workflow configuration
        """
        # Use the class name to find the workflow config
        workflow_name = self.__class__.__name__.lower()
        return self.config.get(workflow_name, {})
    
    async def execute_workflow(self, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow
        
        Args:
            initial_data: The initial data to start the workflow with
            
        Returns:
            The workflow result
        """
        logger.info(f"Executing workflow: {self.__class__.__name__}")
        
        # This method will be implemented by subclasses
        # The Flow API in Crew AI will define the workflow execution
        
        return {}
    
    async def handle_error(self, error: Exception, step: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an error in the workflow
        
        Args:
            error: The error that occurred
            step: The step where the error occurred
            context: The context at the time of the error
            
        Returns:
            Error handling result
        """
        logger.error(f"Error in workflow {self.__class__.__name__} at step {step}: {str(error)}")
        
        # Default error handling - can be overridden by subclasses
        return {
            "status": "error",
            "error": str(error),
            "step": step,
            "context": context
        }
