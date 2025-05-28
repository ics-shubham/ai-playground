# Bedrock Agent 

A client application for interacting with Model Context Protocol (MCP) servers and Amazon Bedrock.

## Features

- Connect to MCP servers via stdio protocol
- Process natural language queries through Amazon Bedrock models
- Execute tools provided by the MCP server

### Environment Variables

The application can be configured using the following environment variables in .env file:

- `MCP_SERVER_PATH`: Path to the MCP server script
- `AWS_REGION`: AWS region for Bedrock
- `BEDROCK_MODEL_ID`: Bedrock model ID to use
- `MAX_TOKENS`: Maximum tokens for model responses
- `TEMPERATURE`: Temperature for model sampling

### Running the Client

Make sure the mcp server in Demo-mcp_servers

```bash
# Run directly
python -m main.py
```

### Project Structure

```
BedRockAgentDemo/
├── __init__.py
├── main.py      # Entry point
├── client.py    # Core client implementation
├── config.py    # Configuration management
└── models.py    # Data models
```

## License

[MIT License](LICENSE)