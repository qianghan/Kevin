#!/usr/bin/env python
"""
Simple test to verify ConfigManager can be imported and used.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.backend.utils.config_manager import ConfigManager

def test_config_manager():
    """Test that ConfigManager works as a singleton."""
    # Create two instances
    config1 = ConfigManager()
    config2 = ConfigManager()
    
    # They should be the same object
    assert config1 is config2
    
    # Get a configuration value
    config = config1.get_all()
    print("Configuration:", config)
    
    print("Test passed: ConfigManager works as a singleton")

if __name__ == "__main__":
    test_config_manager() 