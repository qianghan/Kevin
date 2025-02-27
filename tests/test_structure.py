#!/usr/bin/env python3
"""
Test script to verify the project structure and file organization.
This test is designed to run without requiring external dependencies.
"""

import os
import sys
import unittest
import importlib.util

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestProjectStructure(unittest.TestCase):
    """Test the project structure and file organization."""
    
    def test_directory_structure(self):
        """Test that the expected directory structure exists."""
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Check core directories
        expected_dirs = [
            'src',
            'src/core',
            'src/data',
            'src/models',
            'src/utils',
            'src/web',
            'tests',
            'logs'
        ]
        
        for directory in expected_dirs:
            dir_path = os.path.join(project_dir, directory)
            self.assertTrue(os.path.exists(dir_path), f"Directory {directory} should exist")
    
    def test_core_files_exist(self):
        """Test that essential project files exist."""
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Check essential files
        essential_files = [
            'config.yaml',
            'main.py',
            'README.md',
            'requirements.txt',
            'setup.py'
        ]
        
        for file in essential_files:
            file_path = os.path.join(project_dir, file)
            self.assertTrue(os.path.exists(file_path), f"File {file} should exist")
    
    def test_module_files_exist(self):
        """Test that all module files exist in their expected locations."""
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Check module files
        expected_files = {
            'src/core/': ['__init__.py', 'agent.py', 'document_processor.py', 'agent_setup.py'],
            'src/data/': ['__init__.py', 'scraper.py'],
            'src/models/': ['__init__.py', 'deepseek_client.py'],
            'src/utils/': ['__init__.py', 'logger.py', 'web_search.py'],
            'src/web/': ['__init__.py', 'app.py'],
            'tests/': ['test_structure.py', 'test_webui.py']
        }
        
        for directory, files in expected_files.items():
            dir_path = os.path.join(project_dir, directory)
            for file in files:
                file_path = os.path.join(dir_path, file)
                self.assertTrue(os.path.exists(file_path), f"File {directory}{file} should exist")
    
    def test_module_has_init(self):
        """Test that all Python package directories have __init__.py files."""
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Check for __init__.py in package directories
        package_dirs = ['src', 'src/core', 'src/data', 'src/models', 'src/utils', 'src/web']
        
        for directory in package_dirs:
            init_path = os.path.join(project_dir, directory, '__init__.py')
            self.assertTrue(os.path.exists(init_path), f"Directory {directory} should have __init__.py")
    
    def test_config_format(self):
        """Test that config.yaml is a well-formed YAML file."""
        import yaml
        
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        config_path = os.path.join(project_dir, 'config.yaml')
        
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            # Basic config validation
            self.assertIsInstance(config, dict, "Config should be a dictionary")
            
            # Check for essential config sections
            expected_sections = ['scraping', 'vector_db', 'llm', 'universities', 'workflow']
            for section in expected_sections:
                self.assertIn(section, config, f"Config should have a '{section}' section")
        
        except Exception as e:
            self.fail(f"Error loading or validating config.yaml: {e}")

if __name__ == "__main__":
    unittest.main() 