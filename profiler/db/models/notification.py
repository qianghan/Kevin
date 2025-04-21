"""
Database model for notifications.

This module defines the SQLAlchemy model for storing notification data in the database.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from profiler.db.base_class import Base


class NotificationDB(Base):
    """
    Database model for storing notifications.
    """
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    data = Column(JSON, nullable=True)
    related_entity_id = Column(String, nullable=True, index=True)
    related_entity_type = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, status={self.status})>" 