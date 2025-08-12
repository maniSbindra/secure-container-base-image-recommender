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

To use the web interface, [follow these steps](web_ui/README.md).:

### Command Line Interface (CLI)

TODO: Add CLI usage instructions
