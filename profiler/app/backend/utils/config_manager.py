"""
Configuration Manager for Student Profiler Backend.

This module handles loading, validating, and providing access to
configuration settings from config.yaml.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass

class ConfigManager:
    """
    Manager for loading and accessing configuration settings.
    
    This singleton class handles loading configuration from YAML files,
    environment variables, and providing a consistent interface for 
    accessing configuration values throughout the application.
    """
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._config = {}
        self._initialized = True
        
    def load_config(self, config_path: Optional[str] = None) -> None:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to config file. If None, uses default paths.
        
        Raises:
            ConfigurationError: If configuration cannot be loaded or is invalid.
        """
        if not config_path:
            # Try to locate the config file in standard locations
            base_paths = [
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # backend dir
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config"),
                "/etc/profiler",
            ]
            
            for base in base_paths:
                potential_path = os.path.join(base, "config.yaml")
                if os.path.exists(potential_path):
                    config_path = potential_path
                    break
                    
            if not config_path:
                raise ConfigurationError("Could not find config.yaml in standard locations")
        
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration file: {str(e)}")
            
        # Override with environment variables
        self._load_from_env()
        
        # Validate configuration
        self._validate_config()
    
    def _load_from_env(self) -> None:
        """
        Override configuration with environment variables.
        
        Environment variables should be prefixed with PROFILER_
        and use double underscore as separator for nested keys.
        For example: PROFILER_SERVICES__DEEPSEEK__API_KEY
        """
        prefix = "PROFILER_"
        
        for env_name, env_value in os.environ.items():
            if env_name.startswith(prefix):
                # Remove prefix and split by double underscore
                key_path = env_name[len(prefix):].lower().split("__")
                
                # Navigate to the correct position in the config dict
                current = self._config
                for key in key_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Set the value
                current[key_path[-1]] = self._parse_env_value(env_value)
                logger.debug(f"Override config value from environment: {env_name}")
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable values to appropriate types."""
        # Try to parse as bool
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False
        
        # Try to parse as int
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try to parse as float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _validate_config(self) -> None:
        """
        Validate that the configuration has all required values.
        
        Raises:
            ConfigurationError: If a required configuration value is missing.
        """
        required_keys = [
            ["api", "host"],
            ["api", "port"],
            ["api", "api_key"],
            ["services", "deepseek", "url"],
            ["services", "deepseek", "api_key"],
        ]
        
        for key_path in required_keys:
            if not self.get_value(key_path):
                raise ConfigurationError(f"Missing required configuration value: {'.'.join(key_path)}")
    
    def get_value(self, key_path: list, default=None) -> Any:
        """
        Get configuration value by key path.
        
        Args:
            key_path: List of keys to navigate the config hierarchy.
            default: Default value to return if key is not found.
            
        Returns:
            The configuration value or default if not found.
        """
        if not self._config:
            self.load_config()
            
        current = self._config
        for key in key_path:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        
        return current
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get entire configuration.
        
        Returns:
            Dict containing all configuration values.
        """
        if not self._config:
            self.load_config()
            
        return self._config
    
    def set_value(self, key_path: list, value: Any) -> None:
        """
        Set configuration value by key path.
        
        Note: This does not persist changes to disk.
        
        Args:
            key_path: List of keys to navigate the config hierarchy.
            value: Value to set.
        """
        if not self._config:
            self.load_config()
            
        current = self._config
        for key in key_path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[key_path[-1]] = value


# Create a singleton instance
config = ConfigManager()

# Helper functions for easier access
def get_config(key_path: list, default=None) -> Any:
    """
    Get a configuration value by key path.
    
    Args:
        key_path: List of keys to navigate the config hierarchy.
        default: Default value if key is not found.
        
    Returns:
        Configuration value or default.
    """
    return config.get_value(key_path, default)

def get_api_config(key: str, default=None) -> Any:
    """Helper to get API configuration values."""
    return config.get_value(["api", key], default)

def get_deepseek_config(key: str, default=None) -> Any:
    """Helper to get DeepSeek API configuration values."""
    return config.get_value(["services", "deepseek", key], default)

def get_database_config(key: str = None, default=None) -> Any:
    """Helper to get database configuration values."""
    if key:
        return config.get_value(["database", "chromadb", key], default)
    return config.get_value(["database", "chromadb"], default)

def get_document_config(key: str = None, default=None) -> Any:
    """Helper to get document configuration values."""
    if key:
        return config.get_value(["documents", key], default)
    return config.get_value(["documents"], default)

def get_workflow_config(key: str = None, default=None) -> Any:
    """Helper to get workflow configuration values."""
    if key:
        return config.get_value(["workflow", key], default)
    return config.get_value(["workflow"], default)

def get_logging_config() -> Dict[str, Any]:
    """Helper to get logging configuration."""
    return config.get_value(["logging"], {})

def get_security_config(key: str = None, default=None) -> Any:
    """Helper to get security configuration values."""
    if key:
        return config.get_value(["security", key], default)
    return config.get_value(["security"], default)

def get_websocket_config(key: str = None, default=None) -> Any:
    """Helper to get WebSocket configuration values."""
    if key:
        return config.get_value(["websocket", key], default)
    return config.get_value(["websocket"], default) 