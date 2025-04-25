# Electricity Service

A modular service for checking electricity outage status and billing information.

## Features

- Check electricity outage status by area/locality
- Check billing information by meter number
- Flexible and modular architecture
- Well-documented API

## Usage

### Running the service

```bash
# Run the service with default settings
electricity-service serve

# Run with custom logging level
electricity-service serve --log-level DEBUG
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