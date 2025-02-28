#!/usr/bin/env python3
"""
Logging utilities for the University Information Agent.
"""

import os
import logging
import sys
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pythonjsonlogger.jsonlogger import JsonFormatter

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Set up app logger
app_logger = logging.getLogger('app')
app_logger.setLevel(logging.INFO)
app_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'app.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Set up document logger
doc_logger = logging.getLogger('documents')
doc_logger.setLevel(logging.INFO)
doc_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'documents.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Set up query logger
query_logger = logging.getLogger('queries')
query_logger.setLevel(logging.INFO)
query_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'queries.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Set up agent logger
agent_logger = logging.getLogger('agent')
agent_logger.setLevel(logging.INFO)
agent_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'agent.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Set up API logger
api_logger = logging.getLogger('api')
api_logger.setLevel(logging.INFO)
api_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'api.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Set up workflow logger
workflow_logger = logging.getLogger('workflow')
workflow_logger.setLevel(logging.INFO)
workflow_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'workflow.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Set up console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Set up JSON formatter for file handlers
json_formatter = JsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
app_handler.setFormatter(json_formatter)
doc_handler.setFormatter(json_formatter)
query_handler.setFormatter(json_formatter)
agent_handler.setFormatter(json_formatter)
api_handler.setFormatter(json_formatter)
workflow_handler.setFormatter(json_formatter)

# Add handlers to loggers
app_logger.addHandler(app_handler)
doc_logger.addHandler(doc_handler)
query_logger.addHandler(query_handler)
agent_logger.addHandler(agent_handler)
api_logger.addHandler(api_handler)
workflow_logger.addHandler(workflow_handler)

# Add console handler to app logger
app_logger.addHandler(console_handler)

# Try to set up colored console output, but fall back to regular formatting if unavailable
try:
    import colorlog
    has_color_formatter = hasattr(colorlog, 'ColorFormatter')
    
    if has_color_formatter:
        color_formatter = colorlog.ColorFormatter(
            '%(log_color)s%(levelname)s%(reset)s | %(asctime)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
        console_handler.setFormatter(color_formatter)
    else:
        # Fallback to basic formatter if ColorFormatter isn't available
        basic_formatter = logging.Formatter('%(levelname)s | %(asctime)s | %(name)s | %(message)s',
                                          datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(basic_formatter)
except ImportError:
    # Fallback if colorlog isn't installed
    basic_formatter = logging.Formatter('%(levelname)s | %(asctime)s | %(name)s | %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(basic_formatter)

def get_logger(name):
    """
    Returns a logger with the given name.
    
    Args:
        name: Name for the logger
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    logger.addHandler(console_handler)
    return logger
