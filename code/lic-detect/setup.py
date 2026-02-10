"""
Setup configuration for licitacion_detector package
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="licitacion-detector",
    version="0.1.0",
    author="Bruno - Teramot",
    author_email="bruno@teramot.ai",
    description="Sistema de trading automatizado para arbitrar licitaciones del Tesoro argentino",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/teramot/licitacion-detector",
    project_urls={
        "Bug Tracker": "https://github.com/teramot/licitacion-detector/issues",
        "Documentation": "https://github.com/teramot/licitacion-detector/blob/main/README.md",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pyRofex>=0.2.0",
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "pandas>=1.5.0",
        "numpy>=1.23.0",
        "schedule>=1.1.0",
        "python-dateutil>=2.8.0",
        "sqlalchemy>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.2.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "ipython>=8.0.0",
        ],
        "notifications": [
            "python-telegram-bot>=20.0",
            "sendgrid>=6.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "licitacion-detector=licitacion_detector.main:main",
            "licitacion-quickstart=licitacion_detector.quickstart:main",
        ],
    },
)
