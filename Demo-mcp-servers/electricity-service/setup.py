from setuptools import setup, find_packages

setup(
    name="electricity_service",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "anyio",
        "click",
        "mcp",  # Ensure correct package name for your MCP dependency
    ],
    entry_points={
        "console_scripts": [
            "electricity-service=electricity_service.main:cli",
        ],
    },
    python_requires=">=3.8",
    author="Your Organization",
    author_email="contact@example.com",
    description="Electricity outage and billing information service",
    keywords="electricity, utility, outage, billing",
)