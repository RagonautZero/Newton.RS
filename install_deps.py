#!/usr/bin/env python3
"""Install required dependencies for LogicBridge"""

import subprocess
import sys
import importlib

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--break-system-packages'])
        return True
    except subprocess.CalledProcessError:
        return False

def check_and_install_dependencies():
    """Check and install required dependencies"""
    required_packages = [
        'uvicorn',
        'fastapi',
        'pydantic',
        'sqlalchemy', 
        'click',
        'pyyaml',
        'jsonschema',
        'jinja2',
        'requests'
    ]
    
    installed = []
    failed = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package} already available")
            installed.append(package)
        except ImportError:
            print(f"Installing {package}...")
            if install_package(package):
                print(f"✓ {package} installed successfully")
                installed.append(package)
            else:
                print(f"✗ Failed to install {package}")
                failed.append(package)
    
    print(f"\nSummary: {len(installed)} installed, {len(failed)} failed")
    return len(failed) == 0

if __name__ == "__main__":
    success = check_and_install_dependencies()
    sys.exit(0 if success else 1)