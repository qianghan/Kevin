"""
Document audit logging system.

This module provides functionality for tracking and logging document
operations for security and compliance purposes.
"""

import logging
import json
import uuid
import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class AuditAction(Enum):
    """Document operation actions that can be audited."""
    CREATE = auto()
    READ = auto()
    UPDATE = auto()
    DELETE = auto()
    SHARE = auto()
    DOWNLOAD = auto()
    PRINT = auto()
    ENCRYPT = auto()
    DECRYPT = auto()
    ACCESS_DENIED = auto()
    VERSION_CREATE = auto()
    WATERMARK = auto()
    EXPORT = auto()

class AuditLevel(Enum):
    """Severity/importance levels for audit events."""
    INFO = auto()      # Normal operations
    WARNING = auto()   # Unusual but allowed operations
    ALERT = auto()     # Operations that might require attention
    CRITICAL = auto()  # High-risk operations requiring immediate attention

class AuditRecord:
    """
    Represents a single audit record for a document operation.
    """
    
    def __init__(self, 
                 action: AuditAction,
                 document_id: str,
                 user_id: str,
                 timestamp: Optional[datetime.datetime] = None,
                 level: AuditLevel = AuditLevel.INFO,
                 details: Optional[Dict[str, Any]] = None,
                 ip_address: Optional[str] = None,
                 user_agent: Optional[str] = None,
                 success: bool = True,
                 record_id: Optional[str] = None):
        """
        Initialize a new audit record.
        
        Args:
            action: The action performed on the document
            document_id: ID of the document involved
            user_id: ID of the user who performed the action
            timestamp: When the action occurred (default: now)
            level: Importance level of this audit event
            details: Additional details about the action
            ip_address: IP address of the user
            user_agent: User agent of the client
            success: Whether the action was successful
            record_id: Unique ID for this record (generated if not provided)
        """
        self.action = action
        self.document_id = document_id
        self.user_id = user_id
        self.timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc)
        self.level = level
        self.details = details or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.success = success
        self.record_id = record_id or str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit record to dictionary for storage."""
        return {
            "record_id": self.record_id,
            "action": self.action.name,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.name,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditRecord':
        """Create an audit record from a dictionary."""
        return cls(
            record_id=data.get("record_id"),
            action=AuditAction[data["action"]],
            document_id=data["document_id"],
            user_id=data["user_id"],
            timestamp=datetime.datetime.fromisoformat(data["timestamp"]),
            level=AuditLevel[data["level"]],
            details=data.get("details", {}),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            success=data.get("success", True)
        )

class DocumentAuditLogger:
    """
    Service for logging document operations for auditing purposes.
    
    This service provides methods to log and retrieve audit events
    related to document operations. It supports filtering records
    by various criteria and can generate audit reports.
    """
    
    def __init__(self, 
                 database_url: Optional[str] = None,
                 log_to_file: bool = False,
                 log_file_path: Optional[str] = None):
        """
        Initialize the document audit logger.
        
        Args:
            database_url: URL to the audit log database
            log_to_file: Whether to also log events to a file
            log_file_path: Path to the log file (if log_to_file is True)
        """
        self.database_url = database_url
        self.log_to_file = log_to_file
        self.log_file_path = log_file_path
        self._memory_buffer: List[AuditRecord] = []
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the audit logger, connecting to database if provided."""
        if self._initialized:
            return
        
        # Connect to database if URL provided
        if self.database_url:
            # Database connection would be initialized here
            # This is a placeholder for actual implementation
            logger.info("Connected to audit log database")
        
        # Configure file logging if enabled
        if self.log_to_file and self.log_file_path:
            # Set up file handler for the audit log file
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setLevel(logging.INFO)
            
            # Create a formatter for the log file
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s', 
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            # Add the handler to the logger
            audit_logger = logging.getLogger("document.audit")
            audit_logger.addHandler(file_handler)
            audit_logger.setLevel(logging.INFO)
            
            logger.info(f"Audit logs will be written to {self.log_file_path}")
        
        self._initialized = True
        logger.info("Document audit logger initialized")
    
    async def log_event(self, 
                       action: AuditAction,
                       document_id: str,
                       user_id: str,
                       level: AuditLevel = AuditLevel.INFO,
                       details: Optional[Dict[str, Any]] = None,
                       ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None,
                       success: bool = True) -> str:
        """
        Log a document operation event.
        
        Args:
            action: The action performed on the document
            document_id: ID of the document involved
            user_id: ID of the user who performed the action
            level: Importance level of this audit event
            details: Additional details about the action
            ip_address: IP address of the user
            user_agent: User agent of the client
            success: Whether the action was successful
            
        Returns:
            The ID of the created audit record
        """
        # Ensure logger is initialized
        if not self._initialized:
            await self.initialize()
        
        # Create audit record
        record = AuditRecord(
            action=action,
            document_id=document_id,
            user_id=user_id,
            level=level,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
        
        # Log to console based on level
        log_message = (
            f"Document {action.name} by {user_id} on {document_id}: "
            f"{'SUCCESS' if success else 'FAILURE'}"
        )
        
        if level == AuditLevel.INFO:
            logger.info(log_message)
        elif level == AuditLevel.WARNING:
            logger.warning(log_message)
        elif level == AuditLevel.ALERT:
            logger.error(log_message)
        elif level == AuditLevel.CRITICAL:
            logger.critical(log_message)
        
        # Store the record in memory for now
        self._memory_buffer.append(record)
        
        # If we have a database connection, store there
        if self.database_url:
            # This would be implemented with actual database operations
            pass
        
        # If we're logging to a file, write the record
        if self.log_to_file and self.log_file_path:
            audit_logger = logging.getLogger("document.audit")
            record_json = json.dumps(record.to_dict())
            audit_logger.info(record_json)
        
        return record.record_id
    
    async def get_records(self, 
                         document_id: Optional[str] = None,
                         user_id: Optional[str] = None,
                         action: Optional[AuditAction] = None,
                         level: Optional[AuditLevel] = None,
                         start_time: Optional[datetime.datetime] = None,
                         end_time: Optional[datetime.datetime] = None,
                         success: Optional[bool] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[AuditRecord]:
        """
        Retrieve audit records based on filter criteria.
        
        Args:
            document_id: Filter by document ID
            user_id: Filter by user ID
            action: Filter by action type
            level: Filter by audit level
            start_time: Only include records after this time
            end_time: Only include records before this time
            success: Filter by operation success/failure
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of audit records matching the criteria
        """
        # Ensure logger is initialized
        if not self._initialized:
            await self.initialize()
        
        # Start with all records (from memory in this implementation)
        records = self._memory_buffer.copy()
        
        # Apply filters
        if document_id:
            records = [r for r in records if r.document_id == document_id]
        
        if user_id:
            records = [r for r in records if r.user_id == user_id]
        
        if action:
            records = [r for r in records if r.action == action]
        
        if level:
            records = [r for r in records if r.level == level]
        
        if start_time:
            records = [r for r in records if r.timestamp >= start_time]
        
        if end_time:
            records = [r for r in records if r.timestamp <= end_time]
        
        if success is not None:
            records = [r for r in records if r.success == success]
        
        # Sort by timestamp (newest first)
        records.sort(key=lambda r: r.timestamp, reverse=True)
        
        # Apply limit and offset
        return records[offset:offset + limit]
    
    async def get_record_by_id(self, record_id: str) -> Optional[AuditRecord]:
        """
        Retrieve a specific audit record by ID.
        
        Args:
            record_id: ID of the audit record to retrieve
            
        Returns:
            The audit record if found, None otherwise
        """
        # Ensure logger is initialized
        if not self._initialized:
            await self.initialize()
        
        # Search for record in memory
        for record in self._memory_buffer:
            if record.record_id == record_id:
                return record
        
        # If we have a database, search there
        if self.database_url:
            # This would be implemented with actual database queries
            pass
        
        return None
    
    async def generate_report(self, 
                             document_id: Optional[str] = None,
                             user_id: Optional[str] = None,
                             start_time: Optional[datetime.datetime] = None,
                             end_time: Optional[datetime.datetime] = None,
                             format: str = "json") -> Union[str, Dict[str, Any]]:
        """
        Generate an audit report for compliance or analysis.
        
        Args:
            document_id: Filter by document ID
            user_id: Filter by user ID
            start_time: Start time for the report period
            end_time: End time for the report period
            format: Output format ("json" or "csv")
            
        Returns:
            Report data in the requested format
        """
        # Get records for the report
        records = await self.get_records(
            document_id=document_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000  # Get a large batch for the report
        )
        
        # Process records into a report
        report_data = {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "filters": {
                "document_id": document_id,
                "user_id": user_id,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
            },
            "summary": {
                "total_records": len(records),
                "success_count": sum(1 for r in records if r.success),
                "failure_count": sum(1 for r in records if not r.success),
                "actions": {action.name: 0 for action in AuditAction}
            },
            "records": [r.to_dict() for r in records]
        }
        
        # Count actions
        for record in records:
            report_data["summary"]["actions"][record.action.name] += 1
        
        # Return in requested format
        if format.lower() == "json":
            return json.dumps(report_data, indent=2)
        elif format.lower() == "csv":
            # Simple CSV implementation (could be improved with csv module)
            lines = ["record_id,action,document_id,user_id,timestamp,level,success"]
            for record in records:
                lines.append(
                    f"{record.record_id},{record.action.name},{record.document_id},"
                    f"{record.user_id},{record.timestamp.isoformat()},{record.level.name},"
                    f"{record.success}"
                )
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported report format: {format}")
    
    async def clear_old_records(self, older_than: datetime.datetime) -> int:
        """
        Remove audit records older than the specified time.
        
        Args:
            older_than: Remove records older than this time
            
        Returns:
            Number of records removed
        """
        # Ensure logger is initialized
        if not self._initialized:
            await self.initialize()
        
        # Count records to remove
        initial_count = len(self._memory_buffer)
        
        # Remove old records from memory
        self._memory_buffer = [r for r in self._memory_buffer if r.timestamp >= older_than]
        
        # Calculate how many were removed
        removed_count = initial_count - len(self._memory_buffer)
        
        # If we have a database, remove from there too
        if self.database_url:
            # This would be implemented with actual database operations
            pass
        
        logger.info(f"Removed {removed_count} audit records older than {older_than.isoformat()}")
        return removed_count 