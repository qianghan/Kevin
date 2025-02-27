"""
Logger module for the Canadian University Information Agent.
Provides a centralized logging configuration for the entire application.
"""

import os
import yaml
import logging
import logging.handlers
import colorlog
from datetime import datetime
from typing import Optional, Dict, Any

# Ensure we use the config from the project root
def _get_config_path():
    """Get the path to the config file."""
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, '../..'))
    return os.path.join(project_root, 'config.yaml')

# Load configuration from config.yaml if it exists
def _load_config() -> Dict[str, Any]:
    """Load logging configuration from config.yaml file."""
    default_config = {
        "level": "INFO",
        "console_level": "INFO",
        "file_level": "DEBUG",
        "max_file_size": 10*1024*1024,  # 10 MB
        "backup_count": 5,
        "log_api_calls": True,
        "log_dir": "./logs"
    }
    
    try:
        config_path = _get_config_path()
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                if 'logging' in config:
                    return config['logging']
    except Exception as e:
        print(f"Error loading logging configuration: {e}")
    
    return default_config

# Get logging configuration
config = _load_config()

# Log levels
CRITICAL = logging.CRITICAL  # 50
ERROR = logging.ERROR        # 40
WARNING = logging.WARNING    # 30
INFO = logging.INFO          # 20
DEBUG = logging.DEBUG        # 10

# Create logs directory if it doesn't exist
def _get_log_dir():
    """Get the log directory path, resolving relative paths if needed."""
    log_dir = config.get("log_dir", "./logs")
    
    # If it's a relative path, make it relative to the project root
    if not os.path.isabs(log_dir):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, '../..'))
        log_dir = os.path.join(project_root, log_dir)
    
    # Ensure directory exists
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

# Get log directory
log_dir = _get_log_dir()

# Define log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Configure color formatter for console output
COLOR_FORMAT = '%(log_color)s%(levelname)-8s%(reset)s %(blue)s[%(name)s]%(reset)s %(message)s'
color_formatter = colorlog.ColorFormatter(
    COLOR_FORMAT,
    datefmt=DATE_FORMAT,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)

# Configure root logger
logging.basicConfig(
    level=getattr(logging, config.get("level", "INFO")),
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
)

# Create a rotating file handler
def get_file_handler() -> logging.Handler:
    """Create a file handler for logging that rotates based on size."""
    log_file = f"{log_dir}/university_agent_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=config.get("max_file_size", 10*1024*1024),  # Default: 10 MB
        backupCount=config.get("backup_count", 5),
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    file_handler.setLevel(getattr(logging, config.get("file_level", "DEBUG")))
    return file_handler

# Create a console handler
def get_console_handler() -> logging.Handler:
    """Create a console handler for logging with color formatting."""
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(color_formatter)
    console_handler.setLevel(getattr(logging, config.get("console_level", "INFO")))
    return console_handler

# Global file handler to avoid creating multiple file handlers
_file_handler = get_file_handler()
_console_handler = get_console_handler()

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger with the specified name and level.
    
    Args:
        name: The name of the logger (typically __name__ of the module)
        level: The logging level for this logger (uses application default if None)
    
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    
    if level is not None:
        logger.setLevel(level)
    else:
        # Use default level from config
        logger.setLevel(getattr(logging, config.get("level", "INFO")))
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        logger.addHandler(_file_handler)
        logger.addHandler(_console_handler)
    
    # Make sure the logger doesn't propagate to the root logger
    logger.propagate = False
    
    return logger

def set_log_level(level: int) -> None:
    """
    Set the global log level for the application.
    
    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO)
    """
    # Update root logger
    logging.getLogger().setLevel(level)
    
    # Update console handler
    _console_handler.setLevel(level)

# Create a specific logger for API calls to track all API interactions
api_logger = get_logger('api', getattr(logging, "INFO" if config.get("log_api_calls", True) else "WARNING"))

# Create a specific logger for workflow steps to track the agent's decision-making
workflow_logger = get_logger('workflow', logging.INFO)

# Create a specific logger for scraper to track web scraping operations
scraper_logger = get_logger('scraper', logging.INFO)

# Create a specific logger for document processing
doc_logger = get_logger('document', logging.INFO)

# Log startup information
startup_logger = get_logger('startup')
startup_logger.info("Logging system initialized")
startup_logger.debug(f"Logging configuration: {config}")
startup_logger.debug(f"Log directory: {log_dir}") 