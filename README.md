# Container Base Image Recommendation Tool

A comprehensive tool for analyzing and recommending secure Azure Linux base images from the Microsoft Container Registry (MCR).

## Features

- 🔍 **Image Analysis**: Deep analysis of container images using Syft, Trivy, Gripe, and docker
- 🎯 **Smart Recommendations**: Intelligent matching of user requirements to optimal base images
- 📊 **Registry Scanning**: Automated scanning of Azure Linux images in MCR
- 🛡️ **Security Focus**: Prioritizes secure, vulnerability-free base images
- 🚀 **Language Support**: Supports Python, Node.js, Java, Go, .NET
- 📦 **Package Ecosystem**: Analyzes package managers and installed libraries
- 💾 **Size Optimization**: Considers image size preferences (minimal, balanced, full)

## Installation

### Prerequisites

1. **Docker**: Required for image analysis
   ```bash
   # Install Docker (if not already installed)
   # Follow instructions at https://docs.docker.com/get-docker/
   ```

2. **Syft**: Required for Software Bill of Materials generation
   ```bash
   # Install Syft
   curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

   # Or using Homebrew (macOS)
   brew install syft
   ```
3. **Trivy**: Required for vulnerability scanning and security analysis
   ```bash
   # Install Trivy
   brew install trivy
   ```

## Quick Start

### Web UI

To use the web interface, [follow these steps](web_ui/README.md).

#### Running in VS Code Dev Container

If you're using VS Code with the provided dev container:

1. **Open in Dev Container**:
   - Ensure you have the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed
   - Open the project in VS Code and select "Reopen in Container" when prompted
   - Or use Command Palette (`Ctrl+Shift+P`) → "Dev Containers: Reopen in Container"

2. **Start the Web UI**:
   ```bash
   cd web_ui
   ./start.sh
   ```

3. **Access the Application**:
   - The web server will start on `http://localhost:8080`
   - In VS Code, you'll see a notification to open the port in your browser
   - Click "Open in Browser" or manually navigate to `http://localhost:8080`
   - You can also use the VS Code "Ports" tab to manage forwarded ports

4. **Development Benefits**:
   - All dependencies (Docker, Syft, Trivy) are pre-installed in the container
   - Database will be automatically created if it doesn't exist
   - Hot reload is enabled for development
   - VS Code debugging is fully configured

**Note**: The dev container includes all required tools (Docker, Syft, Trivy) pre-installed, so you can immediately start using the application without additional setup.

### Command Line Interface (CLI)

TODO: Add CLI usage instructions
