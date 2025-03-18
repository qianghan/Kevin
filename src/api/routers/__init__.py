"""
Routers package for Kevin API.

This package contains API route definitions for the FastAPI application.
"""

# Import all routers to make them available for app.py
from . import chat, search, documents, admin

__all__ = ["chat", "search", "documents", "admin"] 