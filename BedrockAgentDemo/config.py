"""
Configuration management for the MCP client application.
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration settings."""
    
    # Server configuration
    server_script_path: str = os.environ.get(
        "MCP_SERVER_PATH", 
        "D:\\AIAgentAWSBedrockDemo\\electricity-service\\main.py"
    )
    
    # AWS configuration
    aws_region: str = os.environ.get("AWS_REGION", "us-east-1")
    
    # Model configuration
    model_id: str = os.environ.get(
        "BEDROCK_MODEL_ID", 
        "us.meta.llama3-2-90b-instruct-v1:0"
    )
    max_tokens: int = int(os.environ.get("MAX_TOKENS", "1000"))
    temperature: float = float(os.environ.get("TEMPERATURE", "0"))
    # top_p: float = float(os.environ.get("TOP_P", "1.0"))
    
    # System prompt for the model
    system_prompt: str = "You are a call center voice assistant, working for a power corporartion in India to assist its customers regarding queries related to power outage and billing details." \
    "                     DO NOT answers any another questions."