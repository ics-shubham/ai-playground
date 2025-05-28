"""Main entry point for the electricity service."""

import sys
import click
from electricity_service.server.server import create_server, run_server

@click.command()
@click.option("--port", default=8000, help="Port value (unused for stdio transport)")
@click.option("--transport", type=click.Choice(["stdio"]), default="stdio", help="Transport mechanism")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]), default="INFO", help="Logging level")
def serve(port: int, transport: str, log_level: str):
    """Start the electricity service server."""
    # Configure logging
    import logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    app = create_server()
    return run_server(app)

sys.exit(serve())