# Container Base Image Recommendation Tool - Architecture

## System Overview

The Container Base Image Recommendation Tool is designed with a modular architecture that provides multiple user interfaces while sharing a common backend and database. The system helps users discover and select secure container base images through intelligent analysis and recommendations.

## High-Level Architecture

```mermaid
flowchart TB
    subgraph UI ["User Interfaces"]
        CLI["CLI Interface"]
        WebUI["Web UI"]
    end

    subgraph Engine ["Core Engine"]
        Core["Recommendation Engine<br/>Image Analyzer<br/>Registry Scanner<br/>Database Layer"]
    end

    subgraph Storage ["Data Storage"]
        SQLite[("SQLite Database")]
    end

    subgraph Tools ["External Tools"]
        ExtTools["Docker<br/>Syft<br/>Trivy<br/>Grype"]
    end

    subgraph Registries ["Container Registries"]
        Regs["Microsoft Container Registry<br/>Docker Hub<br/>Azure Container Registry<br/>Other Registries"]
    end

    UI --> Engine
    Engine --> Storage
    Engine --> Tools
    Engine --> Registries
```

## Architecture Components

### User Interfaces

The system provides two primary interfaces for user interaction:

#### Command Line Interface (CLI)
- **Location**: `src/cli.py`
- **Purpose**: Command-line access for technical users and automation
- **Features**: Image recommendation, analysis, scanning, and database operations

#### Web User Interface
- **Location**: `web_ui/app.py`
- **Purpose**: User-friendly web interface for non-technical users
- **Features**: Interactive dashboard, form-based recommendations, image browser, and scanning interface

### Core Engine

The core engine contains all the business logic and processing components:

- **Recommendation Engine** (`src/recommendation_engine.py`): Intelligent matching of user requirements to optimal base images
- **Image Analyzer** (`src/image_analyzer.py`): Deep analysis of container images using external security tools
- **Registry Scanner** (`src/registry_scanner.py`): Automated scanning and discovery of container images from registries
- **Database Layer** (`src/database.py`): Data persistence, querying, and management

### Data Storage

#### SQLite Database
- **Location**: `azure_linux_images.db`
- **Purpose**: Stores all analyzed image data, vulnerabilities, packages, and metadata from scanned container images
- **Content**: Pre-populated with scanned Azure Linux base images and continuously updated through scanning operations
- **Features**: Lightweight, portable, ACID-compliant database with optimized queries

### External Tools

The system integrates with industry-standard security and analysis tools to scan and analyze container images:

- **Docker**: Container image management and inspection
- **Syft**: Software Bill of Materials (SBOM) generation
- **Trivy**: Vulnerability scanning and security analysis
- **Grype**: Additional security scanning for comprehensive coverage

### Container Registries

The tool scans images from multiple container registries and stores the results in the SQLite database:

- **Microsoft Container Registry (MCR)**: Primary focus on Azure Linux images
- **Docker Hub**: Public container images
- **Azure Container Registry**: Private enterprise registries
- **Other Registries**: Any OCI-compliant container registry

## Key Workflows

### 1. Image Recommendation
Users specify requirements through either the CLI or Web UI. The Core Engine queries the SQLite database (which contains pre-scanned images), applies scoring algorithms, and returns ranked recommendations based on security, compatibility, and user preferences.

### 2. Image Scanning and Storage
The Core Engine scans container images from registries using External Tools, analyzes them for vulnerabilities and software components, then stores all findings in the SQLite database. The repository includes a pre-populated database with analyzed Azure Linux base images.

### 3. Registry Scanning
The system automatically discovers and scans images from Container Registries, performing bulk analysis operations to populate and maintain the SQLite database with current security information and metadata.

## Deployment

The system supports multiple deployment options:
- **Development Container**: Pre-configured VS Code dev container with all dependencies
- **Local Installation**: Manual setup with virtual environments
- **Production**: Docker containerization with WSGI servers

This architecture provides a robust, scalable platform for container security analysis, supporting both technical users through the CLI and business users through the intuitive web interface.

This architecture provides a robust, scalable platform for container security analysis, supporting both technical users through the CLI and business users through the intuitive web interface.
