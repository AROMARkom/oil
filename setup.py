"""
Setup script for WTI Oil Trading Bot
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="wti-oil-trading-bot",
    version="1.0.0",
    author="Trading Bot Team",
    author_email="",
    description="Systematic trading bot for WTI Crude Oil CFD based on volatility expansion strategy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AROMARkom/oil",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "wti-trading-bot=src.trading_bot:main",
        ],
    },
)
