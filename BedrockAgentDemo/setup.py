"""
Setup script for the MCP client package.
"""

from setuptools import setup, find_packages

setup(
    name="AIAgent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "boto3",
        "mcp",
    ],
    entry_points={
        "console_scripts": [
            "aiagent=AIAgent.main:main",
        ],
    },
    python_requires=">=3.8",
    description="A client for the Model Context Protocol",
    author="Your Name",
    author_email="your.email@example.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)