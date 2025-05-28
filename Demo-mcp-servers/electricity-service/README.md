# Electricity Service MCP Server

A modular service for checking electricity outage status and billing information.

## Features

- Check electricity outage status by location
- Check billing information by meter_number

### Running the service

```bash
# Run directly
python -m main.py
```

### Development

The project follows a modular architecture:
    
- `server/`: Contains the MCP server implementation
- `services/`: Business logic for outage and billing services
- `data/`: Data storage and access functions 
- `utils/`: Shared utility functions

## Configuration

The service supports configuration through environment variables and command-line arguments:

- `--port`: The port to run the service on (default: 8000)
- `--transport`: Transport mechanism (default: stdio)
- `--log-level`: Logging level (default: INFO)

## License

[MIT](LICENSE)