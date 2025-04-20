"""
Document security service.

This module provides functionality for security features including virus/malware
scanning for uploaded documents.
"""

import os
import io
import hashlib
import tempfile
import asyncio
import subprocess
from typing import BinaryIO, Dict, Any, Optional, List, Union, Tuple
from pathlib import Path
from enum import Enum
import aiohttp
from urllib.parse import urljoin
import json

from ...utils.logging import get_logger
from ...utils.errors import SecurityError, ConfigurationError

logger = get_logger(__name__)


class ScanStatus(Enum):
    """Status of a virus scan."""
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"
    PENDING = "pending"


class ScanResult:
    """Result of a virus/malware scan."""
    
    def __init__(self, 
                 status: ScanStatus, 
                 filename: str,
                 scan_engine: str,
                 threats: List[str] = None,
                 details: Dict[str, Any] = None):
        """
        Initialize scan result.
        
        Args:
            status: Status of the scan
            filename: Name of the scanned file
            scan_engine: Name of the scanning engine used
            threats: List of threats found, if any
            details: Additional scan details
        """
        self.status = status
        self.filename = filename
        self.scan_engine = scan_engine
        self.threats = threats or []
        self.details = details or {}
        self.timestamp = asyncio.get_event_loop().time()
    
    def is_clean(self) -> bool:
        """Check if the scan result indicates the file is clean."""
        return self.status == ScanStatus.CLEAN
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan result to dictionary for storage or serialization."""
        return {
            "status": self.status.value,
            "filename": self.filename,
            "scan_engine": self.scan_engine,
            "threats": self.threats,
            "details": self.details,
            "timestamp": self.timestamp
        }


class DocumentScanner:
    """Base class for document scanners."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize scanner.
        
        Args:
            config: Configuration for the scanner
        """
        self.config = config or {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the scanner."""
        self._initialized = True
    
    async def scan(self, file_content: BinaryIO, filename: str) -> ScanResult:
        """
        Scan a file for viruses/malware.
        
        Args:
            file_content: Content of the file to scan
            filename: Name of the file
            
        Returns:
            ScanResult with status and details
            
        Raises:
            SecurityError: If scanning fails
        """
        raise NotImplementedError("Subclasses must implement scan method")


class ClamAVScanner(DocumentScanner):
    """Scanner using ClamAV for virus detection."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize ClamAV scanner.
        
        Config options:
            clamd_socket: Path to ClamAV socket (for Unix socket connection)
            clamd_host: ClamAV host (for TCP connection)
            clamd_port: ClamAV port (for TCP connection)
            clamdscan_path: Path to clamdscan executable (for command-line scanning)
            timeout: Timeout for scan operations in seconds
        """
        super().__init__(config)
        self.config.setdefault("timeout", 30)
        self.config.setdefault("clamdscan_path", "clamdscan")
        self._clamd_available = False
    
    async def initialize(self) -> None:
        """Initialize the ClamAV scanner."""
        await super().initialize()
        
        # Check if ClamAV is available
        try:
            # Try to import pyclamd if available
            try:
                import pyclamd
                self._has_pyclamd = True
            except ImportError:
                self._has_pyclamd = False
                logger.warning("pyclamd not available, falling back to command-line scanning")
            
            # If using command-line, check if clamdscan is available
            if not self._has_pyclamd:
                proc = await asyncio.create_subprocess_exec(
                    self.config["clamdscan_path"], "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    version = stdout.decode().strip().split("\n")[0]
                    logger.info(f"ClamAV version: {version}")
                    self._clamd_available = True
                else:
                    logger.warning(f"ClamAV not available: {stderr.decode().strip()}")
            else:
                # Initialize pyclamd
                import pyclamd
                
                if "clamd_socket" in self.config:
                    cd = pyclamd.ClamdUnixSocket(self.config["clamd_socket"])
                else:
                    host = self.config.get("clamd_host", "localhost")
                    port = self.config.get("clamd_port", 3310)
                    cd = pyclamd.ClamdNetworkSocket(host, port)
                
                # Test connection
                version = cd.version()
                logger.info(f"ClamAV version: {version}")
                self._clamd = cd
                self._clamd_available = True
                
        except Exception as e:
            logger.error(f"Failed to initialize ClamAV scanner: {str(e)}")
            self._clamd_available = False
    
    async def scan(self, file_content: BinaryIO, filename: str) -> ScanResult:
        """
        Scan a file using ClamAV.
        
        Args:
            file_content: Content of the file to scan
            filename: Name of the file
            
        Returns:
            ScanResult with status and details
            
        Raises:
            SecurityError: If scanning fails
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._clamd_available:
            logger.warning("ClamAV not available, returning error status")
            return ScanResult(
                status=ScanStatus.ERROR,
                filename=filename,
                scan_engine="ClamAV",
                details={"error": "ClamAV not available"}
            )
        
        try:
            # Save file content to temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Get current position and rewind
                pos = file_content.tell()
                file_content.seek(0)
                
                # Write to temp file
                temp_file.write(file_content.read())
                temp_file.flush()
                
                # Restore position
                file_content.seek(pos)
            
            try:
                # Scan the file
                if self._has_pyclamd:
                    # Use pyclamd
                    scan_result = self._clamd.scan_file(temp_path)
                    
                    if scan_result is None:
                        # File is clean
                        return ScanResult(
                            status=ScanStatus.CLEAN,
                            filename=filename,
                            scan_engine="ClamAV (pyclamd)"
                        )
                    else:
                        # File is infected
                        threats = [details for _, details in scan_result.values()]
                        return ScanResult(
                            status=ScanStatus.INFECTED,
                            filename=filename,
                            scan_engine="ClamAV (pyclamd)",
                            threats=threats,
                            details={"scan_result": scan_result}
                        )
                else:
                    # Use command-line
                    proc = await asyncio.create_subprocess_exec(
                        self.config["clamdscan_path"], "--no-summary", temp_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    
                    # ClamAV returns 1 if virus found, 0 if clean
                    if proc.returncode == 0:
                        return ScanResult(
                            status=ScanStatus.CLEAN,
                            filename=filename,
                            scan_engine="ClamAV (cli)"
                        )
                    elif proc.returncode == 1:
                        # Extract threat names
                        output = stdout.decode()
                        threats = []
                        for line in output.splitlines():
                            if "FOUND" in line:
                                threats.append(line.split("FOUND")[0].strip())
                        
                        return ScanResult(
                            status=ScanStatus.INFECTED,
                            filename=filename,
                            scan_engine="ClamAV (cli)",
                            threats=threats,
                            details={"output": output}
                        )
                    else:
                        # Error in scanning
                        logger.error(f"ClamAV scan error: {stderr.decode()}")
                        return ScanResult(
                            status=ScanStatus.ERROR,
                            filename=filename,
                            scan_engine="ClamAV (cli)",
                            details={"error": stderr.decode()}
                        )
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        except Exception as e:
            logger.error(f"Error scanning file with ClamAV: {str(e)}")
            raise SecurityError(f"Virus scanning failed: {str(e)}")


class VirusTotalScanner(DocumentScanner):
    """Scanner using VirusTotal API for virus/malware detection."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize VirusTotal scanner.
        
        Config options:
            api_key: VirusTotal API key (required)
            api_url: VirusTotal API URL (default: https://www.virustotal.com/api/v3/)
            scan_timeout: Timeout for scan operations in seconds (default: 60)
            allow_upload: Whether to upload files to VirusTotal (default: False)
            max_file_size: Maximum file size to scan in bytes (default: 32MB)
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault("api_url", "https://www.virustotal.com/api/v3/")
        self.config.setdefault("scan_timeout", 60)
        self.config.setdefault("allow_upload", False)
        self.config.setdefault("max_file_size", 32 * 1024 * 1024)  # 32MB
        
        # Validate config
        if "api_key" not in self.config:
            raise ConfigurationError("VirusTotal API key is required")
    
    async def initialize(self) -> None:
        """Initialize the VirusTotal scanner."""
        await super().initialize()
        
        # Validate API key
        if not self.config.get("api_key"):
            logger.error("VirusTotal API key not provided")
            raise ConfigurationError("VirusTotal API key is required")
    
    async def scan(self, file_content: BinaryIO, filename: str) -> ScanResult:
        """
        Scan a file using VirusTotal.
        
        Args:
            file_content: Content of the file to scan
            filename: Name of the file
            
        Returns:
            ScanResult with status and details
            
        Raises:
            SecurityError: If scanning fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get file size
            pos = file_content.tell()
            file_content.seek(0, os.SEEK_END)
            file_size = file_content.tell()
            file_content.seek(0)
            
            # Check file size limit
            if file_size > self.config["max_file_size"]:
                logger.warning(f"File too large for VirusTotal scan: {file_size} bytes")
                return ScanResult(
                    status=ScanStatus.ERROR,
                    filename=filename,
                    scan_engine="VirusTotal",
                    details={"error": "File too large for scanning"}
                )
            
            # Calculate file hash for lookup
            file_content.seek(0)
            file_hash = hashlib.sha256(file_content.read()).hexdigest()
            file_content.seek(pos)  # Restore position
            
            # First, try to look up the file by hash
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-apikey": self.config["api_key"],
                    "Accept": "application/json"
                }
                
                # Check if file has been scanned before
                url = urljoin(self.config["api_url"], f"files/{file_hash}")
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        # File found in VirusTotal
                        data = await response.json()
                        return self._process_vt_response(data, filename)
                    elif response.status == 404:
                        # File not found in VirusTotal
                        if not self.config["allow_upload"]:
                            logger.warning("File not found in VirusTotal and uploads are disabled")
                            return ScanResult(
                                status=ScanStatus.ERROR,
                                filename=filename,
                                scan_engine="VirusTotal",
                                details={"error": "File not found and uploads are disabled"}
                            )
                        
                        # Upload file for scanning
                        file_content.seek(0)
                        files = {
                            "file": (filename, file_content.read())
                        }
                        file_content.seek(pos)  # Restore position
                        
                        upload_url = urljoin(self.config["api_url"], "files")
                        async with session.post(upload_url, headers=headers, data=files) as upload_response:
                            if upload_response.status == 200:
                                upload_data = await upload_response.json()
                                analysis_id = upload_data.get("data", {}).get("id")
                                
                                if not analysis_id:
                                    logger.error("Failed to get analysis ID from VirusTotal")
                                    return ScanResult(
                                        status=ScanStatus.ERROR,
                                        filename=filename,
                                        scan_engine="VirusTotal",
                                        details={"error": "Failed to get analysis ID"}
                                    )
                                
                                # Wait for analysis to complete
                                analysis_url = urljoin(self.config["api_url"], f"analyses/{analysis_id}")
                                for _ in range(3):  # Try a few times
                                    await asyncio.sleep(20)  # Wait for analysis
                                    
                                    async with session.get(analysis_url, headers=headers) as analysis_response:
                                        if analysis_response.status == 200:
                                            analysis_data = await analysis_response.json()
                                            status = analysis_data.get("data", {}).get("attributes", {}).get("status")
                                            
                                            if status == "completed":
                                                return self._process_vt_response(analysis_data, filename)
                                
                                # Analysis not completed in time
                                return ScanResult(
                                    status=ScanStatus.PENDING,
                                    filename=filename,
                                    scan_engine="VirusTotal",
                                    details={"analysis_id": analysis_id}
                                )
                            else:
                                error_text = await upload_response.text()
                                logger.error(f"VirusTotal upload failed: {error_text}")
                                return ScanResult(
                                    status=ScanStatus.ERROR,
                                    filename=filename,
                                    scan_engine="VirusTotal",
                                    details={"error": f"Upload failed: {error_text}"}
                                )
                    else:
                        error_text = await response.text()
                        logger.error(f"VirusTotal API error: {error_text}")
                        return ScanResult(
                            status=ScanStatus.ERROR,
                            filename=filename,
                            scan_engine="VirusTotal",
                            details={"error": f"API error: {error_text}"}
                        )
        
        except Exception as e:
            logger.error(f"Error scanning file with VirusTotal: {str(e)}")
            raise SecurityError(f"Virus scanning failed: {str(e)}")
    
    def _process_vt_response(self, response_data: Dict[str, Any], filename: str) -> ScanResult:
        """Process VirusTotal API response."""
        try:
            # Extract scan results
            attributes = response_data.get("data", {}).get("attributes", {})
            
            if not attributes:
                return ScanResult(
                    status=ScanStatus.ERROR,
                    filename=filename,
                    scan_engine="VirusTotal",
                    details={"error": "No scan attributes found in response"}
                )
            
            # Get detection statistics
            stats = attributes.get("stats", {})
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            total = sum(stats.values())
            
            # Extract detected threats
            results = attributes.get("results", {})
            threats = []
            for engine, result in results.items():
                if result.get("category") in ("malicious", "suspicious"):
                    threat = result.get("result", "Unknown threat")
                    threats.append(f"{engine}: {threat}")
            
            # Determine scan status
            if malicious > 0:
                status = ScanStatus.INFECTED
            elif suspicious > 0:
                # Suspicious files are treated as infected for safety
                status = ScanStatus.INFECTED
            else:
                status = ScanStatus.CLEAN
            
            return ScanResult(
                status=status,
                filename=filename,
                scan_engine="VirusTotal",
                threats=threats,
                details={
                    "stats": stats,
                    "total_engines": total,
                    "malicious_count": malicious,
                    "suspicious_count": suspicious
                }
            )
        except Exception as e:
            logger.error(f"Error processing VirusTotal response: {str(e)}")
            return ScanResult(
                status=ScanStatus.ERROR,
                filename=filename,
                scan_engine="VirusTotal",
                details={"error": f"Error processing response: {str(e)}"}
            )


class DocumentSecurity:
    """
    Service for document security features.
    
    This service provides virus scanning and other security features
    for document uploads.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize document security service.
        
        Args:
            config: Configuration for the security service
        """
        self.config = config or {}
        self._scanners: Dict[str, DocumentScanner] = {}
        self._initialized = False
        
        # Set defaults
        self.config.setdefault("enable_scanning", True)
        self.config.setdefault("block_infected", True)
        self.config.setdefault("default_scanner", "clamav")
        
        # Configure scanners
        if "scanners" not in self.config:
            self.config["scanners"] = {
                "clamav": {"type": "clamav"}
            }
    
    async def initialize(self) -> None:
        """Initialize the document security service."""
        if self._initialized:
            return
        
        logger.info("Initializing document security service")
        
        # Initialize scanners
        if self.config["enable_scanning"]:
            for scanner_name, scanner_config in self.config["scanners"].items():
                scanner_type = scanner_config.get("type", "").lower()
                
                try:
                    if scanner_type == "clamav":
                        scanner = ClamAVScanner(scanner_config)
                    elif scanner_type == "virustotal":
                        scanner = VirusTotalScanner(scanner_config)
                    else:
                        logger.warning(f"Unknown scanner type: {scanner_type}")
                        continue
                    
                    await scanner.initialize()
                    self._scanners[scanner_name] = scanner
                    logger.info(f"Initialized {scanner_type} scanner as '{scanner_name}'")
                except Exception as e:
                    logger.error(f"Failed to initialize {scanner_type} scanner: {str(e)}")
        
        self._initialized = True
        logger.info(f"Document security service initialized with {len(self._scanners)} scanners")
    
    async def scan_document(self, 
                         file_content: BinaryIO, 
                         filename: str,
                         scanner_name: Optional[str] = None) -> ScanResult:
        """
        Scan a document for viruses/malware.
        
        Args:
            file_content: Content of the document to scan
            filename: Name of the document
            scanner_name: Name of the scanner to use (uses default if not specified)
            
        Returns:
            ScanResult with scan status and details
            
        Raises:
            SecurityError: If scanning fails or file is infected and blocking is enabled
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.config["enable_scanning"]:
            logger.info("Document scanning is disabled")
            return ScanResult(
                status=ScanStatus.CLEAN,
                filename=filename,
                scan_engine="none",
                details={"message": "Scanning disabled"}
            )
        
        # Select scanner
        scanner_name = scanner_name or self.config["default_scanner"]
        scanner = self._scanners.get(scanner_name)
        
        if not scanner:
            available_scanners = list(self._scanners.keys())
            if not available_scanners:
                logger.warning("No document scanners available")
                return ScanResult(
                    status=ScanStatus.ERROR,
                    filename=filename,
                    scan_engine="none",
                    details={"error": "No scanners available"}
                )
            
            # Use the first available scanner
            scanner_name = available_scanners[0]
            scanner = self._scanners[scanner_name]
            logger.info(f"Using {scanner_name} scanner (default not available)")
        
        # Scan the document
        logger.info(f"Scanning document '{filename}' with {scanner_name}")
        result = await scanner.scan(file_content, filename)
        
        # Log scan result
        if result.is_clean():
            logger.info(f"Document '{filename}' is clean")
        else:
            if result.status == ScanStatus.INFECTED:
                threats = ", ".join(result.threats) if result.threats else "unknown threat"
                logger.warning(f"Document '{filename}' is infected: {threats}")
                
                if self.config["block_infected"]:
                    raise SecurityError(
                        f"Document contains malware: {threats}",
                        details=result.to_dict()
                    )
            elif result.status == ScanStatus.ERROR:
                logger.error(f"Error scanning document '{filename}': {result.details.get('error', 'unknown error')}")
            else:
                logger.warning(f"Document '{filename}' scan status: {result.status.value}")
        
        return result 