# Container Base Image Recommendation Tool

A comprehensive tool for analyzing and recommending secure container base images from various container registries.

⚠️ **Important**: This tool is designed for **local development and individual use only**. It is **NOT suitable for production deployments**. See the [Architecture Documentation](docs/images/architecture.md) for detailed deployment guidance.

## Demo

![Demo](docs/images/secure-container-base-image-recommender-demo.gif)

*Web UI demonstration: Starting from dev container, getting image recommendations, and comparing alternatives*

## Architecture

For a detailed overview of the system architecture, including the Web UI, SQLite database, CLI interface, and external tool integrations, see the [Architecture Documentation](docs/images/architecture.md).

## Intended Use Case

This tool is specifically designed as a **local development utility** for:

- **Individual developers** selecting secure base images for their containerized applications
- **Security researchers** analyzing container image vulnerabilities in development environments
- **DevOps teams** evaluating base image options during the development phase
- **Learning and experimentation** with container security scanning tools

### Not Suitable For Production

This tool should **NOT** be used for:
- Production container image management systems
- Enterprise-wide deployment or multi-user environments
- Mission-critical security scanning in production pipelines
- High-availability or high-throughput scanning operations

For production use cases, consider enterprise-grade container security platforms that provide proper authentication, authorization, audit logging, and scalability features.

## Features

- 🔍 **Image Analysis**: Deep analysis of container images using Syft, Trivy, Gripe, and docker
- 🎯 **Smart Recommendations**: Intelligent matching of user requirements to optimal base images, including recommendations to replace existing images
- 📊 **Registry Scanning**: Automated scanning of container images from various registries
- 🛡️ **Security Focus**: Prioritizes secure, vulnerability-free base images
- 🚀 **Language Support**: Supports Python, Node.js, Java, Go, .NET
- 📦 **Package Ecosystem**: Analyzes package managers and installed libraries
- 💾 **Size Optimization**: Considers image size preferences (minimal, balanced, full)

### 📌 Quick Links

- Nightly Language Specific Recommendations Report (language specific top secure base images): [`docs/nightly_recommendations.md`](docs/nightly_recommendations.md)
- Web UI Ranking / recommendation logic details: [`docs/recommendations.md`](docs/recommendations.md)
- Database & nightly update details: [`docs/database.md`](docs/database.md)
- Web UI Guide & API endpoints: [`web_ui/README.md`](web_ui/README.md)
- Architecture Overview: [`docs/images/architecture.md`](docs/images/architecture.md)

## Language Specific Recommended Base Images (Nightly)

Nightly scan workflow generates [`docs/nightly_recommendations.md`](docs/nightly_recommendations.md) with the current top images per detected language, ranked by:

1. Lowest critical vulnerabilities
2. Lowest high vulnerabilities
3. Lowest total vulnerabilities
4. Smallest size

Generation details (see [`docs/recommendations.md`](docs/recommendations.md) for rationale & future ideas):
* Script: `scripts/generate_nightly_recommendations_md.py`
* Runs after nightly DB update job
* Commits only when changes detected
* Adjustable result count via `TOP_N` in the script

Regenerate locally after performing a scan:

```bash
python scripts/generate_nightly_recommendations_md.py
less docs/nightly_recommendations.md
```

## Installation

This tool is designed for local development environments only. Choose one of the following installation methods:

### Prerequisites

**Option 1: Use Dev Container (Recommended for Local Development)**

If you're using VS Code, you can use the provided dev container which has all dependencies pre-installed:
- Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- Open the project in VS Code and select "Reopen in Container" when prompted
- All tools (Docker, Syft, Trivy) will be automatically available

**Option 2: Manual Installation on Local Machine**

For local development on your individual machine:

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

To details on Web UI features and usage check [here](web_ui/README.md).

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

## Web UI Screenshots

See full gallery & detailed feature descriptions in the Web UI guide: [`web_ui/README.md`](web_ui/README.md).

Sample dashboard:

![Dashboard](docs/images/dashboard.png)

## SQLite Database & Nightly Updates (Summary)

Project ships with a pre-scanned SQLite DB (`azure_linux_images.db`) updated nightly via GitHub Actions (comprehensive scan + commit via Git LFS).

Quick facts:
* Nightly workflow updates SQLite database only
* Git LFS pointer auto-detected; empty schema created if real DB missing
* You can regenerate locally with the CLI scan command
* Full details, troubleshooting, and regeneration steps: see [`docs/database.md`](docs/database.md)


## Configuring Which Repositories / Images Are Scanned

The list of repositories and/or individual images processed by `--scan` (scan all) is loaded from `config/repositories.txt` if that file exists and contains valid entries. Otherwise a built-in default list of Azure Linux repositories is used.

Supported entry formats (one per non-comment line):

1. Plain Azure Linux repository path (MCR) – e.g. `azurelinux/base/python`.
   * Treated as `mcr.microsoft.com/azurelinux/base/python` with tag enumeration via the MCR API.
2. Fully qualified MCR repository path (no tag) – e.g. `mcr.microsoft.com/azurelinux/distroless/base`.
   * Tag enumeration is performed.
3. Fully qualified image reference with a tag (any registry) – e.g. `docker.io/library/python:3.12-slim`, `ghcr.io/org/runtime:1.0.0`.
   * Scanned as a single image (no tag enumeration).

Notes:
* Lines starting with `#` or blank lines are ignored.
* Non-MCR repositories WITHOUT an explicit tag are currently skipped (multi-tag enumeration not yet implemented). List specific tags instead.
* After editing `config/repositories.txt`, commit the change so CI/nightly scans pick it up.

Example snippet:

```
azurelinux/base/python
azurelinux/distroless/base
docker.io/library/python:3.12-slim
ghcr.io/example/custom-base:1.0.0
```

<!-- Language Specific Recommended Base Images section moved earlier -->
