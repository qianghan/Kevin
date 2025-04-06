"""
Logging utilities for the application.

This module provides logging utilities and configuration.
"""

import logging
import sys
import os
import time
import functools
from typing import Optional, Dict, Any, Callable
import traceback
import json
from datetime import datetime
import uuid
import asyncio

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The logger name, typically __name__
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    return logger


def log_execution_time(logger: logging.Logger):
    """
    Decorator to log function execution time.
    
    Args:
        logger: Logger to use for logging execution time
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def log_function_call(logger: logging.Logger):
    """
    Decorator to log function calls with arguments.
    
    Args:
        logger: Logger to use for logging
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            arg_str = ", ".join([str(a) for a in args[1:]])  # Skip self
            kwarg_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            all_args = ", ".join(filter(None, [arg_str, kwarg_str]))
            logger.debug(f"Calling {func.__name__}({all_args})")
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            arg_str = ", ".join([str(a) for a in args[1:]])  # Skip self
            kwarg_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            all_args = ", ".join(filter(None, [arg_str, kwarg_str]))
            logger.debug(f"Calling {func.__name__}({all_args})")
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def configure_logging(log_level: str = "INFO", log_to_file: bool = False, log_file: str = None) -> None:
    """
    Configure global logging settings.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to a file
        log_file: Log file path (default: logs/app.log)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        if not log_file:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "app.log")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Log configuration
    get_logger(__name__).info(f"Logging configured with level {log_level}")


class JsonFormatter(logging.Formatter):
    """JSON formatter for logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            JSON formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "log_id": str(uuid.uuid4())
        }
        
        # Include exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Include extra fields if available
        if hasattr(record, "props"):
            log_data.update(record.props)
        
        return json.dumps(log_data)


def configure_json_logging(log_level: str = "INFO", log_to_file: bool = False, log_file: str = None) -> None:
    """
    Configure global logging with JSON formatting.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to a file
        log_file: Log file path (default: logs/app.json)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create JSON formatter
    json_formatter = JsonFormatter()
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(json_formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        if not log_file:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "app.json")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(json_formatter)
        root_logger.addHandler(file_handler)
    
    # Log configuration
    get_logger(__name__).info(f"JSON logging configured with level {log_level}")


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context to log records.
    
    This adapter allows adding context to logs by including additional fields.
    """
    
    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        """
        Initialize the adapter.
        
        Args:
            logger: The logger to adapt
            extra: Extra context to include in all logs
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process the log message and kwargs.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Processed message and kwargs
        """
        # Ensure 'extra' is present in kwargs
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        # Add 'props' if not present
        if 'props' not in kwargs['extra']:
            kwargs['extra']['props'] = {}
        
        # Add adapter extras to props
        if self.extra:
            kwargs['extra']['props'].update(self.extra)
        
        return msg, kwargs


def get_context_logger(name: str, context: Optional[Dict[str, Any]] = None) -> LoggerAdapter:
    """
    Get a logger with context.
    
    Args:
        name: The logger name, typically __name__
        context: Optional context to include in all logs
        
    Returns:
        Logger adapter with context
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context) 