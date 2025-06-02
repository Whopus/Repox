#!/usr/bin/env python3
"""
Core functionality test for Repox v0.2.0
Tests imports, configuration, and basic functionality without API calls
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test all core imports."""
    print("🧪 Testing imports...")
    try:
        # Core imports
        from src.repox import Repox, RepoxConfig, RepoxAssistant
        from src.repox.api import SearchResult, ContextResult, AnswerResult
        from src.repox.models import AIModel, ModelFactory
        from src.repox.locator import FileLocator
        from src.repox.filter import SmartFilter
        from src.repox.context import ContextBuilder
        from src.repox.repository import RepositoryAnalyzer
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_configuration():
    """Test configuration system."""
    print("🧪 Testing configuration system...")
    try:
        from src.repox.config import RepoxConfig
        
        # Test default configuration
        config = RepoxConfig()
        print(f"✅ Default config created")
        
        # Test presets
        default_config = RepoxConfig.create_default()
        large_repo_config = RepoxConfig.create_for_large_repo()
        dev_config = RepoxConfig.create_for_development()
        print(f"✅ All presets created")
        
        # Test serialization
        config_dict = config.to_dict()
        config_json = config.to_json()
        print(f"✅ Serialization working")
        
        # Test update
        config.update(max_file_size=200000, verbose=True)
        print(f"✅ Configuration update working")
        
        # Test validation (will be False without API key)
        is_valid = config.is_valid()
        print(f"✅ Validation working (valid: {is_valid})")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_repository_analyzer():
    """Test repository analyzer without API calls."""
    print("🧪 Testing repository analyzer...")
    try:
        from src.repox.repository import RepositoryAnalyzer
        from src.repox.config import RepoxConfig
        
        config = RepoxConfig()
        analyzer = RepositoryAnalyzer("/workspace/Repox", config)
        
        # Test basic methods
        structure = analyzer.get_repository_structure()
        file_sizes = analyzer.get_file_sizes()
        processable_files = analyzer.get_processable_files()
        
        print(f"✅ Repository structure: {len(structure)} chars")
        print(f"✅ File sizes: {len(file_sizes)} files")
        print(f"✅ Processable files: {len(processable_files)} files")
        
        return True
    except Exception as e:
        print(f"❌ Repository analyzer error: {e}")
        return False

def test_file_locator():
    """Test file locator without API calls."""
    print("🧪 Testing file locator...")
    try:
        from src.repox.locator import FileLocator
        from src.repox.config import RepoxConfig
        from src.repox.models import ModelFactory
        
        config = RepoxConfig()
        
        # Create a mock model for testing
        class MockModel:
            def generate_sync(self, *args, **kwargs):
                return type('MockResponse', (), {'content': '{"files": [], "reasoning": "test"}'})()
        
        mock_model = MockModel()
        locator = FileLocator("/workspace/Repox", config, mock_model)
        
        # Test that locator was created successfully
        print(f"✅ File locator created successfully")
        print(f"✅ Repository path: {locator.repo_path}")
        print(f"✅ Has repository analyzer: {hasattr(locator, 'repository_analyzer')}")
        
        return True
    except Exception as e:
        print(f"❌ File locator error: {e}")
        return False

def test_cli_help():
    """Test CLI help commands."""
    print("🧪 Testing CLI help...")
    try:
        import subprocess
        
        # Test main help
        result = subprocess.run(
            ["python", "-m", "src.repox.cli", "--help"],
            cwd="/workspace/Repox",
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "Repox" in result.stdout:
            print("✅ CLI help working")
            return True
        else:
            print(f"❌ CLI help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI help error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 REPOX v0.2.0 CORE FUNCTIONALITY TEST")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Repository Analyzer", test_repository_analyzer),
        ("File Locator", test_file_locator),
        ("CLI Help", test_cli_help),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 {name}")
        print("-" * 30)
        success = test_func()
        results.append((name, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL CORE TESTS PASSED!")
        print("🚀 Repox v0.2.0 core functionality is working!")
        
        if not os.getenv('OPENAI_API_KEY'):
            print("\n💡 To test full functionality with AI features:")
            print("   1. Set OPENAI_API_KEY environment variable")
            print("   2. Run: python -m src.repox.cli ask 'What does this repo do?'")
        
        return 0
    else:
        print(f"\n❌ {len(results) - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())