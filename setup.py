"""
U-ITE Package Setup Configuration
===================================
Setup script for building and distributing the U-ITE package.
This file defines the package metadata, dependencies, and entry points
for installation via pip.

This is the traditional setup.py approach (compatible with older pip versions).
For modern Python packaging, consider also maintaining a pyproject.toml file.

Features:
- Package metadata (name, version, description)
- Automatic package discovery in src/ directory
- Dependency management
- Console script entry point creation
- Python version requirements
"""

from setuptools import setup, find_packages

# ============================================================================
# Package Configuration
# ============================================================================
setup(
    # ------------------------------------------------------------------------
    # Package Metadata
    # ------------------------------------------------------------------------
    name="u-ite",                              # PyPI package name
    version="0.1.0",                            # Follows Semantic Versioning
    description="Continuous Network Observability Platform",
    long_description=open("README.md").read(),  # Use README as long description
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/u-ite",  # Project homepage
    license="MIT",                               # Open source license
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha, 4 - Beta, 5 - Production/Stable
        "Development Status :: 4 - Beta",
        
        # Indicate who your project is intended for
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        
        # Pick your license as you wish
        "License :: OSI Approved :: MIT License",
        
        # Specify the Python versions you support here
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        
        # Operating systems
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        
        # Topics
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    keywords="network monitoring, diagnostics, observability, cli",
    
    # ------------------------------------------------------------------------
    # Package Discovery
    # ------------------------------------------------------------------------
    # Find all packages in the src/ directory
    packages=find_packages(where="src"),
    package_dir={"": "src"},                     # Root package is in src/
    
    # Include non-Python files (like schema.sql)
    include_package_data=True,
    package_data={
        "uite.storage": ["schema.sql"],          # Include database schema
    },
    
    # ------------------------------------------------------------------------
    # Dependencies
    # ------------------------------------------------------------------------
    install_requires=[
        "click>=8.0.0",      # CLI framework
        "requests>=2.25.0",   # HTTP requests for diagnostics
        "tabulate>=0.8.0",    # Pretty table formatting
        # Optional: matplotlib and numpy for graphing
        # Users can install these separately if they want graphs
    ],
    
    # Optional dependencies (install with: pip install u-ite[graphs])
    extras_require={
        "graphs": [
            "matplotlib>=3.5.0",
            "numpy>=1.21.0",
        ],
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
    },
    
    # ------------------------------------------------------------------------
    # Entry Points
    # ------------------------------------------------------------------------
    # Create console scripts that users can run
    entry_points={
        "console_scripts": [
            # Creates 'uite' command that calls uite.cli:cli
            "uite = uite.cli:cli",
        ],
    },
    
    # ------------------------------------------------------------------------
    # Python Version Requirements
    # ------------------------------------------------------------------------
    python_requires=">=3.8",
    
    # ------------------------------------------------------------------------
    # Project URLs
    # ------------------------------------------------------------------------
    project_urls={
        "Bug Reports": "https://github.com/yourusername/u-ite/issues",
        "Source": "https://github.com/yourusername/u-ite",
        "Documentation": "https://docs.u-ite.io",
    },
    
    # ------------------------------------------------------------------------
    # ZIP Safe
    # ------------------------------------------------------------------------
    # Set to False if the package needs to access files (like schema.sql)
    zip_safe=False,
)
