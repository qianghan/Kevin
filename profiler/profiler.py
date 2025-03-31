#!/usr/bin/env python3
"""
Student Profiler Service Manager

This script manages the Student Profiler services, providing commands to:
- Start/stop the API server, UI development server
- View and manage logs
- Check service status

Usage:
    python profiler.py <command> [options]

Commands:
    start       Start services
    stop        Stop services
    status      Check service status
    logs        View logs
    clean       Clean temporary files
    help        Show this help message
"""

import os
import sys
import subprocess
import signal
import time
import argparse
import json
import shutil
import logging
from pathlib import Path
import datetime
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("profiler")

# Define project paths
ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = ROOT_DIR / "profiler" / "app" / "backend"
UI_DIR = ROOT_DIR / "profiler" / "app" / "ui"
LOGS_DIR = BACKEND_DIR / "logs"
PID_DIR = ROOT_DIR / ".pid"
CONFIG_FILE = BACKEND_DIR / "config.yaml"

# Ensure necessary directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PID_DIR.mkdir(parents=True, exist_ok=True)

# Service definitions
SERVICES = {
    "api": {
        "name": "API Server",
        "description": "FastAPI backend server",
        "start_cmd": ["uvicorn", "profiler.app.backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        "cwd": ROOT_DIR,
        "pid_file": PID_DIR / "api.pid",
        "log_file": LOGS_DIR / "api.log",
        "env": {"PYTHONPATH": str(ROOT_DIR)},
    },
    "ui": {
        "name": "UI Server",
        "description": "Next.js frontend development server",
        "start_cmd": ["npm", "run", "dev"],
        "cwd": UI_DIR,
        "pid_file": PID_DIR / "ui.pid",
        "log_file": LOGS_DIR / "ui.log",
        "env": {},
    }
}

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Student Profiler Service Manager")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start services")
    start_parser.add_argument("services", nargs="*", choices=list(SERVICES.keys()) + ["all"], 
                              default=["all"], help="Services to start (default: all)")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop services")
    stop_parser.add_argument("services", nargs="*", choices=list(SERVICES.keys()) + ["all"], 
                             default=["all"], help="Services to stop (default: all)")
    
    # Status command
    subparsers.add_parser("status", help="Check service status")
    
    # Logs command
    logs_parser = subparsers.add_parser("logs", help="View logs")
    logs_parser.add_argument("service", choices=list(SERVICES.keys()), help="Service to view logs for")
    logs_parser.add_argument("-f", "--follow", action="store_true", help="Follow log output")
    logs_parser.add_argument("-n", "--lines", type=int, default=50, help="Number of lines to show (default: 50)")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean temporary files")
    clean_parser.add_argument("--logs", action="store_true", help="Clean log files")
    clean_parser.add_argument("--pids", action="store_true", help="Clean PID files")
    clean_parser.add_argument("--all", action="store_true", help="Clean everything")
    
    return parser.parse_args()

def start_service(service_id: str) -> bool:
    """
    Start a service.
    
    Args:
        service_id: ID of the service to start
        
    Returns:
        True if service was started successfully, False otherwise
    """
    if service_id not in SERVICES:
        logger.error(f"Unknown service: {service_id}")
        return False
    
    service = SERVICES[service_id]
    
    # Check if already running
    if is_service_running(service_id):
        logger.info(f"{service['name']} is already running")
        return True
    
    # Prepare environment
    env = os.environ.copy()
    env.update(service["env"])
    
    # Start the service
    try:
        with open(service["log_file"], "a") as log_file:
            log_file.write(f"\n--- Starting {service['name']} at {datetime.datetime.now()} ---\n\n")
            
            process = subprocess.Popen(
                service["start_cmd"],
                cwd=service["cwd"],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True
            )
            
            # Save PID
            with open(service["pid_file"], "w") as pid_file:
                pid_file.write(str(process.pid))
            
            logger.info(f"Started {service['name']} (PID: {process.pid})")
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if still running
            if process.poll() is not None:
                logger.error(f"Failed to start {service['name']}. Check logs: {service['log_file']}")
                return False
                
            return True
    except Exception as e:
        logger.error(f"Error starting {service['name']}: {str(e)}")
        return False

def stop_service(service_id: str) -> bool:
    """
    Stop a service.
    
    Args:
        service_id: ID of the service to stop
        
    Returns:
        True if service was stopped successfully, False otherwise
    """
    if service_id not in SERVICES:
        logger.error(f"Unknown service: {service_id}")
        return False
    
    service = SERVICES[service_id]
    pid_file = service["pid_file"]
    
    if not pid_file.exists():
        logger.info(f"{service['name']} is not running")
        return True
    
    try:
        # Read PID
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        
        # Send SIGTERM
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            logger.info(f"Stopping {service['name']} (PID: {pid})...")
            
            # Wait for it to terminate
            for _ in range(10):
                try:
                    os.kill(pid, 0)  # Check if process exists
                    time.sleep(0.5)
                except OSError:
                    break
            else:
                # If still running, SIGKILL
                logger.warning(f"{service['name']} not responding, sending SIGKILL...")
                try:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except OSError:
                    pass
        except OSError:
            logger.info(f"{service['name']} (PID: {pid}) already stopped")
        
        # Remove PID file
        pid_file.unlink(missing_ok=True)
        
        # Log the stop
        with open(service["log_file"], "a") as log_file:
            log_file.write(f"\n--- Stopped {service['name']} at {datetime.datetime.now()} ---\n\n")
            
        return True
    except Exception as e:
        logger.error(f"Error stopping {service['name']}: {str(e)}")
        return False

def is_service_running(service_id: str) -> bool:
    """
    Check if a service is running.
    
    Args:
        service_id: ID of the service to check
        
    Returns:
        True if service is running, False otherwise
    """
    if service_id not in SERVICES:
        return False
    
    service = SERVICES[service_id]
    pid_file = service["pid_file"]
    
    if not pid_file.exists():
        return False
    
    try:
        # Read PID
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        
        # Check if process exists
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            # Process doesn't exist, clean up PID file
            pid_file.unlink(missing_ok=True)
            return False
    except Exception:
        return False

def get_service_status() -> Dict[str, Dict[str, Any]]:
    """
    Get status of all services.
    
    Returns:
        Dictionary with service status information
    """
    status = {}
    
    for service_id, service in SERVICES.items():
        running = is_service_running(service_id)
        pid = None
        
        if running:
            try:
                with open(service["pid_file"], "r") as f:
                    pid = int(f.read().strip())
            except Exception:
                pass
        
        status[service_id] = {
            "name": service["name"],
            "running": running,
            "pid": pid,
            "log_file": str(service["log_file"]),
        }
    
    return status

def view_logs(service_id: str, follow: bool = False, lines: int = 50) -> None:
    """
    Display logs for a service.
    
    Args:
        service_id: ID of the service to display logs for
        follow: Whether to follow log output
        lines: Number of lines to show
    """
    if service_id not in SERVICES:
        logger.error(f"Unknown service: {service_id}")
        return
    
    service = SERVICES[service_id]
    log_file = service["log_file"]
    
    if not log_file.exists():
        logger.error(f"No logs found for {service['name']}")
        return
    
    if follow:
        try:
            cmd = ["tail", "-n", str(lines), "-f", str(log_file)]
            process = subprocess.Popen(cmd)
            print(f"Showing logs for {service['name']}. Press Ctrl+C to exit.")
            process.wait()
        except KeyboardInterrupt:
            process.terminate()
            print("\nExited log view.")
    else:
        try:
            cmd = ["tail", "-n", str(lines), str(log_file)]
            subprocess.run(cmd)
        except Exception as e:
            logger.error(f"Error viewing logs: {str(e)}")

def clean_files(clean_logs: bool = False, clean_pids: bool = False, clean_all: bool = False) -> None:
    """
    Clean temporary files.
    
    Args:
        clean_logs: Whether to clean log files
        clean_pids: Whether to clean PID files
        clean_all: Whether to clean everything
    """
    if clean_all:
        clean_logs = True
        clean_pids = True
    
    if clean_logs:
        for file in LOGS_DIR.glob("*.log"):
            try:
                file.unlink()
                logger.info(f"Removed log file: {file}")
            except Exception as e:
                logger.error(f"Error removing log file {file}: {str(e)}")
    
    if clean_pids:
        for file in PID_DIR.glob("*.pid"):
            try:
                file.unlink()
                logger.info(f"Removed PID file: {file}")
            except Exception as e:
                logger.error(f"Error removing PID file {file}: {str(e)}")

def print_status_table(status: Dict[str, Dict[str, Any]]) -> None:
    """
    Print formatted status table.
    
    Args:
        status: Dictionary with service status information
    """
    # Calculate column widths
    col1_width = max(len("SERVICE"), max(len(s) for s in status.keys()))
    col2_width = max(len("STATUS"), 8)
    col3_width = max(len("PID"), 6)
    col4_width = max(len("LOG FILE"), max(len(s["log_file"]) for s in status.values()))
    
    # Print header
    print(f"{'SERVICE'.ljust(col1_width)} | {'STATUS'.ljust(col2_width)} | {'PID'.ljust(col3_width)} | {'LOG FILE'}")
    print(f"{'-' * col1_width}-+-{'-' * col2_width}-+-{'-' * col3_width}-+-{'-' * col4_width}")
    
    # Print services
    for service_id, info in status.items():
        status_str = "RUNNING" if info["running"] else "STOPPED"
        pid_str = str(info["pid"]) if info["pid"] else "-"
        print(f"{service_id.ljust(col1_width)} | {status_str.ljust(col2_width)} | {pid_str.ljust(col3_width)} | {info['log_file']}")

def main():
    """Main entry point."""
    args = parse_args()
    
    if args.command == "start":
        services_to_start = args.services
        if "all" in services_to_start:
            services_to_start = list(SERVICES.keys())
        
        for service_id in services_to_start:
            start_service(service_id)
    
    elif args.command == "stop":
        services_to_stop = args.services
        if "all" in services_to_stop:
            services_to_stop = list(SERVICES.keys())
        
        for service_id in services_to_stop:
            stop_service(service_id)
    
    elif args.command == "status":
        status = get_service_status()
        print_status_table(status)
    
    elif args.command == "logs":
        view_logs(args.service, args.follow, args.lines)
    
    elif args.command == "clean":
        clean_files(args.logs, args.pids, args.all)
    
    else:
        print(__doc__)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
        sys.exit(1) 