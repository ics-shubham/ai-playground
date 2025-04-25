# MCP Client

A client application for interacting with Model Context Protocol (MCP) servers and Amazon Bedrock.

## Features

- Connect to MCP servers via stdio protocol
- Process natural language queries through Amazon Bedrock models
- Execute tools provided by the MCP server
- Interactive chat interface

### Environment Variables

The application can be configured using the following environment variables:

- `MCP_SERVER_PATH`: Path to the MCP server script
- `AWS_REGION`: AWS region for Bedrock
- `BEDROCK_MODEL_ID`: Bedrock model ID to use
- `MAX_TOKENS`: Maximum tokens for model responses
- `TEMPERATURE`: Temperature for model sampling

### Running the Client

```bash
# Run directly
python -m electricity-service.main

# Or use the installed script
mcp-client
```

## Development

### Project Structure

```
mcp_client/
├── __init__.py
├── electricity-service.py      # Entry point
├── client.py    # Core client implementation
├── config.py    # Configuration management
└── models.py    # Data models
```

## License

[MIT License](LICENSE)