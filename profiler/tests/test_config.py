"""
Tests for the configuration management system.

This module tests:
- Config loading from files
- Environment variable overrides
- Config validation
- Helper functions for accessing config values
"""

import os
import tempfile
import pytest
import yaml
from pathlib import Path

from profiler.app.backend.utils.config_manager import (
    ConfigManager,
    ConfigurationError,
    get_config,
    get_api_config,
    get_deepseek_config,
    get_database_config,
    get_document_config,
    get_workflow_config,
    get_logging_config,
    get_security_config,
    get_websocket_config
)


# Test fixture for creating temporary config files
@pytest.fixture
def temp_config_file():
    """Create a temporary config.yaml file for testing."""
    config_data = {
        "api": {
            "host": "127.0.0.1",
            "port": 8000,
            "api_key": "test_api_key",
            "timeout": 30
        },
        "services": {
            "deepseek": {
                "url": "https://test-api.deepseek.com",
                "api_key": "test_deepseek_key",
                "model": "test-model",
                "batch_size": 5
            }
        },
        "database": {
            "chromadb": {
                "host": "localhost",
                "port": 8001,
                "collection": "test_collection"
            }
        },
        "logging": {
            "level": "INFO",
            "file": "test.log"
        }
    }
    
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        yaml.dump(config_data, temp_file)
        temp_path = temp_file.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


# Test config loading from file
def test_load_config_from_file(temp_config_file):
    """Test loading configuration from a file."""
    # Create a new instance to avoid singleton issues in tests
    config_manager = ConfigManager()
    config_manager._initialized = False
    config_manager._config = {}
    
    # Load config from the temporary file
    config_manager.load_config(temp_config_file)
    
    # Check if values were loaded correctly
    assert config_manager.get_value(["api", "host"]) == "127.0.0.1"
    assert config_manager.get_value(["api", "port"]) == 8000
    assert config_manager.get_value(["services", "deepseek", "url"]) == "https://test-api.deepseek.com"
    assert config_manager.get_value(["database", "chromadb", "collection"]) == "test_collection"


# Test default values
def test_get_value_with_default(temp_config_file):
    """Test getting config values with defaults."""
    config_manager = ConfigManager()
    config_manager._initialized = False
    config_manager._config = {}
    config_manager.load_config(temp_config_file)
    
    # Existing value
    assert config_manager.get_value(["api", "port"]) == 8000
    
    # Non-existing value with default
    assert config_manager.get_value(["api", "non_existent"], default=42) == 42
    
    # Nested non-existing value with default
    assert config_manager.get_value(["non_existent", "key"], default="default") == "default"


# Test environment variable overrides
def test_environment_variable_overrides(temp_config_file):
    """Test that environment variables override config file values."""
    # Set environment variables
    os.environ["PROFILER_API__PORT"] = "9000"
    os.environ["PROFILER_SERVICES__DEEPSEEK__API_KEY"] = "env_var_key"
    os.environ["PROFILER_NEW_SECTION__NEW_KEY"] = "new_value"
    
    try:
        # Create a new instance to avoid singleton issues
        config_manager = ConfigManager()
        config_manager._initialized = False
        config_manager._config = {}
        
        # Load config
        config_manager.load_config(temp_config_file)
        
        # Check overridden values
        assert config_manager.get_value(["api", "port"]) == 9000  # Integer conversion
        assert config_manager.get_value(["services", "deepseek", "api_key"]) == "env_var_key"
        
        # Check new value added via env var
        assert config_manager.get_value(["new_section", "new_key"]) == "new_value"
        
        # Original values should still be there
        assert config_manager.get_value(["api", "host"]) == "127.0.0.1"
    finally:
        # Clean up environment variables
        del os.environ["PROFILER_API__PORT"]
        del os.environ["PROFILER_SERVICES__DEEPSEEK__API_KEY"]
        del os.environ["PROFILER_NEW_SECTION__NEW_KEY"]


# Test environment variable type conversion
def test_env_var_type_conversion():
    """Test that environment variables are converted to appropriate types."""
    os.environ["PROFILER_TEST__INT_VAL"] = "42"
    os.environ["PROFILER_TEST__FLOAT_VAL"] = "3.14"
    os.environ["PROFILER_TEST__BOOL_TRUE"] = "true"
    os.environ["PROFILER_TEST__BOOL_FALSE"] = "false"
    os.environ["PROFILER_TEST__STRING_VAL"] = "hello"
    
    try:
        # Create a new instance
        config_manager = ConfigManager()
        config_manager._initialized = False
        config_manager._config = {}
        
        # Load config (without file, just env vars)
        try:
            config_manager.load_config()
        except ConfigurationError:
            # Expected, since required config may be missing
            pass
        
        # Manually load from env
        config_manager._load_from_env()
        
        # Check type conversions
        assert isinstance(config_manager.get_value(["test", "int_val"]), int)
        assert config_manager.get_value(["test", "int_val"]) == 42
        
        assert isinstance(config_manager.get_value(["test", "float_val"]), float)
        assert config_manager.get_value(["test", "float_val"]) == 3.14
        
        assert isinstance(config_manager.get_value(["test", "bool_true"]), bool)
        assert config_manager.get_value(["test", "bool_true"]) is True
        
        assert isinstance(config_manager.get_value(["test", "bool_false"]), bool)
        assert config_manager.get_value(["test", "bool_false"]) is False
        
        assert isinstance(config_manager.get_value(["test", "string_val"]), str)
        assert config_manager.get_value(["test", "string_val"]) == "hello"
    finally:
        # Clean up
        del os.environ["PROFILER_TEST__INT_VAL"]
        del os.environ["PROFILER_TEST__FLOAT_VAL"]
        del os.environ["PROFILER_TEST__BOOL_TRUE"]
        del os.environ["PROFILER_TEST__BOOL_FALSE"]
        del os.environ["PROFILER_TEST__STRING_VAL"]


# Test config validation
def test_config_validation(temp_config_file):
    """Test validation of required configuration values."""
    # Create a valid config
    config_manager = ConfigManager()
    config_manager._initialized = False
    config_manager._config = {}
    config_manager.load_config(temp_config_file)
    
    # Should validate without errors
    config_manager._validate_config()
    
    # Make a required value missing
    config_manager._config["services"]["deepseek"]["api_key"] = None
    
    # Should raise ConfigurationError
    with pytest.raises(ConfigurationError) as excinfo:
        config_manager._validate_config()
    
    assert "Missing required configuration value" in str(excinfo.value)


# Test helper functions
def test_helper_functions(temp_config_file):
    """Test the helper functions for accessing configuration values."""
    # First ensure the singleton has the right config
    config_manager = ConfigManager()
    config_manager._initialized = False
    config_manager._config = {}
    config_manager.load_config(temp_config_file)
    
    # Test general helper
    assert get_config(["api", "port"]) == 8000
    assert get_config(["non_existent"], default="default") == "default"
    
    # Test specific helpers
    assert get_api_config("port") == 8000
    assert get_deepseek_config("url") == "https://test-api.deepseek.com"
    assert get_database_config("collection") == "test_collection"
    
    # Test helpers that return sections
    assert isinstance(get_logging_config(), dict)
    assert get_logging_config()["level"] == "INFO"
    
    # Test helpers for sections that don't exist in the test config
    assert get_document_config() is None
    assert get_document_config("key", default="default") == "default"
    assert get_workflow_config() is None
    assert get_security_config() is None
    assert get_websocket_config() is None


# Test singleton behavior
def test_singleton_behavior():
    """Test that ConfigManager behaves as a singleton."""
    # Create two instances
    config1 = ConfigManager()
    config2 = ConfigManager()
    
    # They should be the same object
    assert config1 is config2
    
    # Changing one should affect the other
    config1._config = {"test": "value"}
    assert config2._config == {"test": "value"}


# Test setting values at runtime
def test_set_value():
    """Test setting configuration values at runtime."""
    config_manager = ConfigManager()
    config_manager._initialized = False
    config_manager._config = {}
    
    # Set a new value
    config_manager.set_value(["new", "key"], "value")
    assert config_manager.get_value(["new", "key"]) == "value"
    
    # Set a nested value that requires creating intermediate dicts
    config_manager.set_value(["a", "b", "c", "d"], 42)
    assert config_manager.get_value(["a", "b", "c", "d"]) == 42 