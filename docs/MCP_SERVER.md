# Container Image Recommendation MCP Server

This directory contains a Model Context Protocol (MCP) server that provides AI assistants with access to secure container base image recommendations.

## Overview

The MCP server exposes the container image recommendation functionality through the standardized Model Context Protocol, allowing AI assistants and development tools to query for secure base image recommendations directly.

## Features

### Available Tools

1. **recommend_images** - Get container base image recommendations based on requirements
   - Input: language, version, packages, size_preference, security_level, limit
   - Output: Ranked list of recommended images with scores and reasoning

2. **analyze_image** - Analyze a specific container image and get recommendations for alternatives  
   - Input: image_name, limit
   - Output: Analysis of the image with alternative recommendations

3. **search_images** - Search for container images by language, security level, or other criteria
   - Input: language, security_filter, max_vulnerabilities, limit
   - Output: List of matching images with metadata

### Available Resources

1. **database://stats** - Current database statistics and summary
2. **database://languages** - List of supported programming languages and their statistics

## Container Image

The MCP server is packaged as a Docker container and published to GitHub Container Registry:

```
ghcr.io/manisbindra/secure-container-base-image-recommender/mcp-server:latest
```

### Tags Available

- `latest` - Latest stable version from main branch
- `main` - Latest build from main branch  
- `v1.0.0` - Specific version tags
- `pr-*` - Pull request builds for testing

## Usage

### Using with VS Code

1. **Install the MCP Extension** (when available) or use compatible MCP client extensions

2. **Configure the MCP Server**:
   
   Add to your VS Code settings or MCP client configuration:
   
   ```json
   {
     "mcp": {
       "servers": {
         "container-recommendations": {
           "command": "docker",
           "args": [
             "run", 
             "--rm", 
             "-i",
             "ghcr.io/manisbindra/secure-container-base-image-recommender/mcp-server:latest"
           ],
           "env": {}
         }
       }
     }
   }
   ```

3. **Alternative: Local Development Setup**
   
   For development, you can run the server locally:
   
   ```json
   {
     "mcp": {
       "servers": {
         "container-recommendations": {
           "command": "python",
           "args": ["mcp_server.py"],
           "cwd": "/path/to/secure-container-base-image-recommender",
           "env": {}
         }
       }
     }
   }
   ```

### Using with Other MCP Clients

The server follows the standard MCP protocol and can be used with any compatible MCP client:

```bash
# Run the container interactively
docker run -i ghcr.io/manisbindra/secure-container-base-image-recommender/mcp-server:latest

# Send MCP requests via stdin/stdout
echo '{"jsonrpc": "2.0", "id": "1", "method": "tools/list"}' | docker run -i ghcr.io/manisbindra/secure-container-base-image-recommender/mcp-server:latest
```

### Example MCP Interactions

#### Initialize the Server
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "vscode",
      "version": "1.0.0"
    }
  }
}
```

#### Get Image Recommendations
```json
{
  "jsonrpc": "2.0",
  "id": "2", 
  "method": "tools/call",
  "params": {
    "name": "recommend_images",
    "arguments": {
      "language": "python",
      "version": "3.12",
      "packages": ["flask", "requests"],
      "size_preference": "minimal",
      "security_level": "high",
      "limit": 5
    }
  }
}
```

#### Analyze Existing Image
```json
{
  "jsonrpc": "2.0",
  "id": "3",
  "method": "tools/call", 
  "params": {
    "name": "analyze_image",
    "arguments": {
      "image_name": "docker.io/library/python:3.12-slim",
      "limit": 3
    }
  }
}
```

## Running Locally

### Prerequisites

- Docker (for containerized usage)
- Python 3.12+ (for local development)
- Required external tools: syft, grype, trivy

### Local Development

```bash
# Clone the repository
git clone https://github.com/maniSbindra/secure-container-base-image-recommender.git
cd secure-container-base-image-recommender

# Install dependencies
pip install -r requirements.txt

# Run the MCP server
python mcp_server.py
```

### Building the Container

```bash
# Build the container image
docker build -t container-mcp-server .

# Run the container
docker run -i container-mcp-server

# Test the container
echo '{"jsonrpc": "2.0", "id": "1", "method": "tools/list"}' | docker run -i container-mcp-server
```

## Environment Variables

- `MCP_DB_PATH` - Path to the SQLite database (default: `/app/azure_linux_images.db`)
- `PYTHONPATH` - Python path for imports (default: `/app/src`)

## Security Considerations

- The container runs as a non-root user (`mcpuser`)
- Uses security scanning tools (Trivy, Grype) for vulnerability analysis
- Database is read-only in the container
- No network dependencies required for basic recommendations (uses pre-scanned database)

## Troubleshooting

### Common Issues

1. **Container fails to start**
   - Check that Docker is installed and running
   - Verify the image was pulled correctly: `docker pull ghcr.io/manisbindra/secure-container-base-image-recommender/mcp-server:latest`

2. **No recommendations returned**
   - Verify the database is present and has data
   - Check the language parameter matches supported languages (python, nodejs, java, go, dotnet)

3. **MCP client connection issues**
   - Ensure the MCP client supports the protocol version (2024-11-05)
   - Check that stdin/stdout communication is working
   - Verify the container can be run interactively

### Debug Mode

Run with debug logging:

```bash
docker run -i -e PYTHONUNBUFFERED=1 ghcr.io/manisbindra/secure-container-base-image-recommender/mcp-server:latest
```

### Health Check

The container includes a health check that verifies database connectivity:

```bash
docker run --rm ghcr.io/manisbindra/secure-container-base-image-recommender/mcp-server:latest python -c "
import sys
sys.path.append('/app/src')
from database import ImageDatabase
db = ImageDatabase('/app/azure_linux_images.db')
stats = db.get_vulnerability_statistics()
db.close()
print('Health check passed')
print(f'Database contains {stats.get(\"total_images\", 0)} images')
"
```

## Development

### Adding New Tools

To add new MCP tools, modify the `_handle_tools_list` method in `mcp_server.py` and implement the corresponding handler method.

### Testing

```bash
# Run tests
pytest tests/

# Test MCP server specifically
python -c "
import asyncio
import sys
sys.path.append('src')
from mcp_server import MCPServer

async def test():
    server = MCPServer()
    request = {'jsonrpc': '2.0', 'id': 'test', 'method': 'tools/list'}
    response = await server.handle_request(request)
    print(f'Tools available: {len(response[\"result\"][\"tools\"])}')

asyncio.run(test())
"
```

### Container Registry

The container is automatically built and published to GitHub Container Registry via GitHub Actions when:
- Changes are pushed to main branch
- A new release is created
- Manual workflow dispatch is triggered

## License

This project follows the same license as the main repository.