#!/usr/bin/env python3
"""
Installation verification script for Repox
Run this script after installation to verify everything is working correctly.
"""

import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def check_package_import():
    """Check if repox package can be imported."""
    print("\n📦 Checking package import...")
    try:
        import repox
        print("✅ Repox package imported successfully")
        print(f"   Version: {getattr(repox, '__version__', 'unknown')}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import repox: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are available."""
    print("\n🔗 Checking dependencies...")
    dependencies = [
        'repomix',
        'openai', 
        'click',
        'pydantic',
        'rich',
        'pathspec'
    ]
    
    all_good = True
    for dep in dependencies:
        try:
            spec = importlib.util.find_spec(dep)
            if spec is not None:
                print(f"✅ {dep}")
            else:
                print(f"❌ {dep} not found")
                all_good = False
        except ImportError:
            print(f"❌ {dep} not found")
            all_good = False
    
    return all_good

def check_cli_command():
    """Check if repox CLI command is available."""
    print("\n🖥️  Checking CLI command...")
    try:
        result = subprocess.run(['repox', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ repox CLI command is working")
            print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ repox CLI command failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ repox CLI command timed out")
        return False
    except FileNotFoundError:
        print("❌ repox CLI command not found in PATH")
        return False
    except Exception as e:
        print(f"❌ Error running repox CLI: {e}")
        return False

def main():
    """Run all verification checks."""
    print("🔍 Repox Installation Verification")
    print("=" * 40)
    
    checks = [
        check_python_version,
        check_package_import,
        check_dependencies,
        check_cli_command
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    print("\n" + "=" * 40)
    print("📊 Summary:")
    
    if all(results):
        print("🎉 All checks passed! Repox is ready to use.")
        print("\n💡 Try running: repox --help")
        return 0
    else:
        print("⚠️  Some checks failed. Please review the output above.")
        print("\n🔧 Installation help:")
        print("   pip install -e .")
        print("   pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())