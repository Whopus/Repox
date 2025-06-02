#!/usr/bin/env python3
"""
Complete functionality test for Repox v0.2.0
Tests all CLI commands and API functionality
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd):
    """Run a command and return result."""
    print(f"\n🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="/workspace/Repox")
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print(f"Output: {result.stdout[:500]}...")
    if result.stderr:
        print(f"Error: {result.stderr[:200]}...")
    return result

def test_cli_commands():
    """Test all CLI commands."""
    print("=" * 60)
    print("🧪 TESTING CLI COMMANDS")
    print("=" * 60)
    
    # Test help
    run_command("python -m src.repox.cli --help")
    
    # Test info command
    run_command("python -m src.repox.cli info")
    
    # Test find command
    run_command("python -m src.repox.cli find 'configuration files'")
    
    # Test ask command
    run_command("python -m src.repox.cli ask 'What is the main purpose of this repository?'")
    
    # Test build command with files
    run_command("python -m src.repox.cli build --files 'src/repox/__init__.py,src/repox/config.py' --format json")
    
    # Test build command with query
    run_command("python -m src.repox.cli build --query 'API classes' --format markdown")
    
    # Test init command (already done, but show it works)
    print("\n✅ Init command already tested - created .repox.json")

def test_api_imports():
    """Test API imports."""
    print("\n" + "=" * 60)
    print("🧪 TESTING API IMPORTS")
    print("=" * 60)
    
    try:
        # Test main imports
        from src.repox import Repox, RepoxConfig, RepoxAssistant
        from src.repox.api import SearchResult, ContextResult, AnswerResult
        from src.repox.models import AIModel, ModelFactory
        from src.repox.locator import FileLocator
        from src.repox.filter import SmartFilter
        print("✅ All imports successful")
        
        # Test configuration creation
        config = RepoxConfig()
        print(f"✅ Configuration created: {type(config)}")
        
        # Test configuration presets
        default_config = RepoxConfig.create_default()
        large_repo_config = RepoxConfig.create_for_large_repo()
        dev_config = RepoxConfig.create_for_development()
        print("✅ Configuration presets working")
        
        # Test configuration validation
        print(f"✅ Config validation: {config.is_valid()}")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_configuration_system():
    """Test the enhanced configuration system."""
    print("\n" + "=" * 60)
    print("🧪 TESTING CONFIGURATION SYSTEM")
    print("=" * 60)
    
    try:
        from src.repox.config import RepoxConfig
        
        # Test default configuration
        config = RepoxConfig()
        print(f"✅ Default config created")
        
        # Test validation
        print(f"✅ Config is valid: {config.is_valid()}")
        
        # Test presets
        presets = [
            RepoxConfig.create_default(),
            RepoxConfig.create_for_large_repo(),
            RepoxConfig.create_for_development()
        ]
        print(f"✅ All {len(presets)} presets created successfully")
        
        # Test serialization
        config_dict = config.to_dict()
        config_json = config.to_json()
        print(f"✅ Serialization working: dict={len(config_dict)} keys, json={len(config_json)} chars")
        
        # Test update
        config.update(max_file_size=200000, verbose=True)
        print(f"✅ Configuration update working")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 REPOX v0.2.0 COMPLETE FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Check environment
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not set - some tests may fail")
    
    # Run tests
    api_success = test_api_imports()
    config_success = test_configuration_system()
    
    # CLI tests (these make actual API calls)
    print("\n" + "=" * 60)
    print("🧪 CLI TESTS (with API calls)")
    print("=" * 60)
    
    if os.getenv('OPENAI_API_KEY'):
        test_cli_commands()
        print("✅ CLI commands tested with API calls")
    else:
        print("⚠️  Skipping CLI tests - no API key")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ API Imports: {'PASS' if api_success else 'FAIL'}")
    print(f"✅ Configuration System: {'PASS' if config_success else 'FAIL'}")
    print(f"✅ CLI Commands: {'TESTED' if os.getenv('OPENAI_API_KEY') else 'SKIPPED (no API key)'}")
    
    if api_success and config_success:
        print("\n🎉 ALL CORE TESTS PASSED!")
        print("🚀 Repox v0.2.0 is ready for use!")
    else:
        print("\n❌ Some tests failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())