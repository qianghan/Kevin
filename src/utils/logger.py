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

# Dictionary to store all loggers for easier access
LOGGERS = {}

# Set up app logger
app_logger = logging.getLogger('app')
app_logger.setLevel(logging.INFO)
app_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'app.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
LOGGERS['app'] = app_logger

# Set up document logger
doc_logger = logging.getLogger('documents')
doc_logger.setLevel(logging.INFO)
doc_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'documents.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
LOGGERS['documents'] = doc_logger

# Set up query logger
query_logger = logging.getLogger('queries')
query_logger.setLevel(logging.INFO)
query_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'queries.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
LOGGERS['queries'] = query_logger

# Set up agent logger
agent_logger = logging.getLogger('agent')
agent_logger.setLevel(logging.INFO)
agent_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'agent.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
LOGGERS['agent'] = agent_logger

# Set up API logger
api_logger = logging.getLogger('api')
api_logger.setLevel(logging.INFO)
api_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'api.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
LOGGERS['api'] = api_logger

# Set up workflow logger
workflow_logger = logging.getLogger('workflow')
workflow_logger.setLevel(logging.INFO)
workflow_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'workflow.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
LOGGERS['workflow'] = workflow_logger

# Set up scraper logger
scraper_logger = logging.getLogger('scraper')
scraper_logger.setLevel(logging.INFO)
scraper_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'scraper.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
LOGGERS['scraper'] = scraper_logger

# Set up search logger
search_logger = logging.getLogger('search')
search_logger.setLevel(logging.INFO)
search_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'search.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
LOGGERS['search'] = search_logger

# Set up db logger
db_logger = logging.getLogger('db')
db_logger.setLevel(logging.INFO)
db_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'db.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
LOGGERS['db'] = db_logger

# Set up web logger
web_logger = logging.getLogger('web')
web_logger.setLevel(logging.INFO)
web_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'web.log'),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
LOGGERS['web'] = web_logger

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
scraper_handler.setFormatter(json_formatter)
search_handler.setFormatter(json_formatter)
db_handler.setFormatter(json_formatter)
web_handler.setFormatter(json_formatter)

# Add handlers to loggers
app_logger.addHandler(app_handler)
doc_logger.addHandler(doc_handler)
query_logger.addHandler(query_handler)
agent_logger.addHandler(agent_handler)
api_logger.addHandler(api_handler)
workflow_logger.addHandler(workflow_handler)
scraper_logger.addHandler(scraper_handler)
search_logger.addHandler(search_handler)
db_logger.addHandler(db_handler)
web_logger.addHandler(web_handler)

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
    if name in LOGGERS:
        return LOGGERS[name]
    
    logger = logging.getLogger(name)
    logger.addHandler(console_handler)
    return logger

def set_log_level(level, logger_name=None):
    """
    Set the log level for a specific logger or all loggers.
    
    Args:
        level: Log level (e.g., logging.DEBUG, logging.INFO, etc. or string 'DEBUG', 'INFO')
        logger_name: Name of the logger to set the level for, or None to set for all loggers
        
    Returns:
        None
    """
    # Convert string level to logging constant if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    if logger_name:
        if logger_name in LOGGERS:
            LOGGERS[logger_name].setLevel(level)
        else:
            logging.getLogger(logger_name).setLevel(level)
    else:
        # Set level for all loggers
        for logger in LOGGERS.values():
            logger.setLevel(level)
        
        # Set level for console handler
        console_handler.setLevel(level)

def disable_logging():
    """
    Disable all logging.
    """
    logging.disable(logging.CRITICAL)

def enable_logging():
    """
    Enable logging after it has been disabled.
    """
    logging.disable(logging.NOTSET)

def get_all_loggers():
    """
    Get all available loggers.
    
    Returns:
        Dictionary of logger names and logger objects
    """
    return LOGGERS
