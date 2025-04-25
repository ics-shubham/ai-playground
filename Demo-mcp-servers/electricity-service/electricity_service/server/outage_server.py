"""Server implementation for the electricity service."""

import anyio
import logging
from typing import Optional
import mcp.types as types
from mcp.server.lowlevel import Server

from electricity_service.services.outage_service import check_outage
from electricity_service.services.billing_service import check_billing

logger = logging.getLogger(__name__)


def create_server(name: str = "electricity-info-checker") -> Server:
    """Create and configure the MCP server instance.
    
    Args:
        name: The name of the server.
        
    Returns:
        A configured Server instance.
    """
    app = Server(name)

    @app.call_tool()
    async def handle_tool(name: str, arguments: dict) -> list[types.TextContent]:
        """Handle tool calls from the client.
        
        Args:
            name: The name of the tool to call.
            arguments: The arguments to pass to the tool.
            
        Returns:
            A list of TextContent responses.
            
        Raises:
            ValueError: If the tool name is unknown.
        """
        logger.info(f"Tool call received: {name} with arguments: {arguments}")
        
        try:
            if name == "check_outage":
                return await handle_check_outage(arguments)
            elif name == "check_billing_status":
                return await handle_check_billing(arguments)
            else:
                error_msg = f"Unknown tool: {name}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        except Exception as e:
            logger.exception(f"Error handling tool call: {e}")
            return [types.TextContent(
                type="text", 
                text=f"Error: An error occurred while processing your request: {str(e)}"
            )]

    async def handle_check_outage(arguments: dict) -> list[types.TextContent]:
        """Handle check_outage tool calls.
        
        Args:
            arguments: The arguments for the outage check.
            
        Returns:
            A list of TextContent responses.
        """
        if "area" not in arguments:
            return [types.TextContent(
                type="text", 
                text="Error: Please provide an area to check for outages."
            )]
        
        area_input = arguments["area"]
        response = await check_outage(area_input)
        return [types.TextContent(type="text", text=response)]

    async def handle_check_billing(arguments: dict) -> list[types.TextContent]:
        """Handle check_billing_status tool calls.
        
        Args:
            arguments: The arguments for the billing check.
            
        Returns:
            A list of TextContent responses.
        """
        if "meter_number" not in arguments:
            return [types.TextContent(
                type="text", 
                text="Error: Please provide a meter number to check billing status."
            )]
        
        meter_number = arguments["meter_number"]
        response = await check_billing(meter_number)
        return [types.TextContent(type="text", text=response)]

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List available tools and their schemas.
        
        Returns:
            A list of Tool descriptors.
        """
        return [
            types.Tool(
                name="check_outage",
                description="Check electricity outage status for a given area or locality",
                inputSchema={
                    "type": "object",
                    "required": ["area"],
                    "properties": {
                        "area": {
                            "type": "string",
                            "description": "Area or locality name to check outage status (e.g. Sector 18, Rajendra Nagar)",
                        }
                    },
                },
            ),
            types.Tool(
                name="check_billing_status",
                description="Check electricity billing status by meter number",
                inputSchema={
                    "type": "object",
                    "required": ["meter_number"],
                    "properties": {
                        "meter_number": {
                            "type": "string",
                            "description": "10-digit meter number prefixed with 'UP' (e.g. UP7284651023)",
                        }
                    },
                },
            ),
        ]
    
    return app


def run_server(app: Server) -> int:
    """Run the server with the specified transport.
    
    Args:
        app: The configured Server instance.
        
    Returns:
        Exit code (0 for success).
    """
    # For now we only support STDIO
    from mcp.server.stdio import stdio_server

    async def arun():
        """Async runner for the server."""
        logger.info("Starting electricity service server")
        async with stdio_server() as streams:
            await app.run(
                streams[0], streams[1], app.create_initialization_options()
            )

    anyio.run(arun)
    return 0