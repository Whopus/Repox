#!/usr/bin/env python3
"""
Setup script for Repox - AI-Powered Code Context Management Assistant
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Repox - AI-Powered Code Context Management Assistant"

# Read requirements from requirements.txt if it exists
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Fallback to hardcoded requirements
    return [
        'repomix>=0.1.0',
        'openai>=1.0.0',
        'click>=8.0.0',
        'pydantic>=2.0.0',
        'rich>=13.0.0',
        'pathspec>=0.11.0',
    ]

setup(
    name="repox",
    version="0.2.0",
    author="OpenHands AI",
    author_email="openhands@all-hands.dev",
    description="AI-Powered Code Context Management Assistant",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Whopus/Repox",
    project_urls={
        "Bug Tracker": "https://github.com/Whopus/Repox/issues",
        "Documentation": "https://github.com/Whopus/Repox#readme",
        "Source Code": "https://github.com/Whopus/Repox",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Documentation",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "repox=repox.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "ai",
        "code-analysis",
        "repository",
        "context-management",
        "llm",
        "openai",
        "code-assistant",
        "developer-tools",
    ],
)