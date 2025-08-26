# Container Security Prompts

## Overview

This directory contains GitHub Copilot prompts that enable users to easily request container security recommendations and analysis through AI assistants. When used with the MCP server, these prompts provide structured guidance for common container security tasks.

## Available Prompts

### 1. Recommend Secure Base Image (`recommend-secure-base-image.md`)
Get recommendations for secure container base images based on your programming language and requirements.

**Use Case**: When starting a new project or seeking secure alternatives for your current base image.

**Key Features**:
- Language-specific recommendations
- Security level customization
- Size preference options
- Vulnerability analysis

### 2. Analyze Container Security (`analyze-container-security.md`)
Analyze your current container image for security vulnerabilities and get recommendations for more secure alternatives.

**Use Case**: Security assessment of existing container images in your project.

**Key Features**:
- Current image vulnerability analysis
- Security risk assessment
- Alternative recommendations
- Migration guidance

### 3. Search Secure Images (`search-secure-images.md`)
Search the security database for container images that meet specific security and functional requirements.

**Use Case**: Finding images with specific security constraints or zero vulnerabilities.

**Key Features**:
- Criteria-based search
- Security threshold filtering
- Language and version filtering
- Comprehensive security metrics

### 4. Container Migration Guide (`container-migration-guide.md`)
Get guidance on migrating from your current container setup to more secure alternatives with step-by-step instructions.

**Use Case**: Planned migration to more secure container infrastructure.

**Key Features**:
- Migration planning
- Step-by-step instructions
- Compatibility assessment
- Risk mitigation strategies

### 5. Zero Vulnerability Images (`zero-vulnerability-images.md`)
Find container base images with zero critical and high severity vulnerabilities for maximum security.

**Use Case**: High-security environments requiring zero-vulnerability images.

**Key Features**:
- Maximum security focus
- Zero critical/high vulnerability filtering
- Enterprise-ready options
- Compliance considerations

## Using with MCP Server

When using the MCP server, these prompts are automatically exposed through the `prompts/list` and `prompts/get` endpoints:

```bash
# List available prompts
echo '{"jsonrpc": "2.0", "id": "1", "method": "prompts/list"}' | \
  docker run --rm -i ghcr.io/manisbindra/secure-container-base-image-recommender/mcp-server:latest

# Get a specific prompt
echo '{"jsonrpc": "2.0", "id": "2", "method": "prompts/get", "params": {"name": "recommend-secure-base-image"}}' | \
  docker run --rm -i ghcr.io/manisbindra/secure-container-base-image-recommender/mcp-server:latest
```

## Using with GitHub Copilot

These prompts are designed to work seamlessly with GitHub Copilot and other AI assistants:

1. **Direct Reference**: Copy the prompt text and customize it for your specific needs
2. **MCP Integration**: Use with MCP-compatible AI clients for automated access
3. **Template Usage**: Use as templates for creating custom security prompts

## Example Usage

### Getting Python Recommendations
```
I need a secure container base image recommendation for a Python 3.12 application with flask and requests packages. I prefer minimal size with high security level.
```

### Analyzing Current Image
```
Please analyze the security of docker.io/library/python:3.12-slim and recommend more secure alternatives for my Python application.
```

### Finding Zero-Vulnerability Images
```
Find Python images with zero critical and high vulnerabilities for production deployment.
```

## Integration with AI Assistants

These prompts are optimized for:
- **GitHub Copilot**: Natural language interaction with container security recommendations
- **VS Code Extensions**: MCP-compatible extensions for direct integration
- **Command Line Tools**: CLI tools supporting MCP protocol
- **Custom AI Applications**: Any application implementing MCP client functionality

## Customization

Each prompt can be customized by:
1. Modifying the language requirements
2. Adjusting security levels
3. Specifying package dependencies
4. Setting size preferences
5. Adding compliance requirements

The prompts are designed to be flexible templates that can be adapted for specific organizational needs and security policies.