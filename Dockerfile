# Multi-stage Dockerfile for Container Image Recommendation MCP Server
FROM python:3.12-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install external tools required for image analysis (optional for MCP server)
RUN curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin || echo "Syft installation failed, continuing..." && \
    curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin || echo "Grype installation failed, continuing..." && \
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin || echo "Trivy installation failed, continuing..."

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY mcp_server.py .
COPY azure_linux_images.db .

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

USER mcpuser

# Verify core functionality (tools are optional)
RUN python -c "import sys; sys.path.append('/app/src'); from database import ImageDatabase; print('✓ Database access working')"

# Expose port for potential HTTP interface (optional)
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app/src
ENV MCP_DB_PATH=/app/azure_linux_images.db

# Default command runs the MCP server
CMD ["python", "mcp_server.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.append('/app/src'); from database import ImageDatabase; db = ImageDatabase('/app/azure_linux_images.db'); stats = db.get_vulnerability_statistics(); db.close(); print('Health check passed')" || exit 1

# Labels for metadata
LABEL org.opencontainers.image.title="Container Image Recommendation MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for secure container base image recommendations"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="Container Security Team"
LABEL org.opencontainers.image.source="https://github.com/maniSbindra/secure-container-base-image-recommender"
LABEL org.opencontainers.image.documentation="https://github.com/maniSbindra/secure-container-base-image-recommender/blob/main/README.md"