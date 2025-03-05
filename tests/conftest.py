import os
import sys
import pytest
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Configure pytest
def pytest_configure(config):
    """Configure pytest."""
    # Add any custom markers
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async"
    )

# Create a fixture for the project root
@pytest.fixture(scope="session")
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent

# Create a fixture for the test data directory
@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Get the test data directory."""
    return project_root / "tests" / "data"

# Create a fixture for the vector database directory
@pytest.fixture(scope="session")
def vectordb_dir(project_root):
    """Get the vector database directory."""
    return project_root / "data" / "vectordb" 