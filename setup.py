from setuptools import setup, find_packages

setup(
    name="u-ite",
    version="0.1.0",
    description="Continuous Network Observability Platform",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click>=8.0.0",
        "requests>=2.25.0",
        "tabulate>=0.8.0",
    ],
    entry_points={
        "console_scripts": [
            "uite = uite.cli:cli",
        ],
    },
    python_requires=">=3.8",
)
