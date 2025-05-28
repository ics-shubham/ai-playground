#!/usr/bin/env python
"""
MCP Client Application

A client application that interacts with the Model Context Protocol (MCP) server
and Amazon Bedrock to process natural language queries.
"""

import asyncio
import logging

from client import MCPClient
from config import Config


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def main():
    """Main entry point for the MCP client application."""
    setup_logging()
    logger = logging.getLogger("mcp_client")
    
    # Load configuration
    config = Config()
    
    logger.info("Starting MCP Client")
    client = MCPClient(config)
    
    try:
        logger.info(f"Connecting to MCP server at: {config.server_script_path}")
        await client.connect()
        logger.info("Connection established")
        
        await client.run_interactive_chat()
    except Exception as e:
        logger.exception(f"Error in main application: {str(e)}")
    finally:
        logger.info("Shutting down client")
        await client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())