# Multi-stage Dockerfile for Container Image Recommendation MCP Server
# Build stage using recommended Azure Linux base image
FROM mcr.microsoft.com/azurelinux/base/python:3.12 AS builder

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Runtime stage using recommended Azure Linux base image
FROM mcr.microsoft.com/azurelinux/base/python:3.12 AS runtime

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/lib/python3.12/site-packages /usr/lib/python3.12/site-packages

# Copy source code
COPY src/ ./src/
COPY mcp_server.py .
COPY azure_linux_images.db .

# Use existing non-root user for security
RUN chown -R nonroot:nonroot /app

USER nonroot

# Verify core functionality
RUN python3 -c "import sys; sys.path.append('/app/src'); from database import ImageDatabase; print('✓ Database access working')"

# Expose port for potential HTTP interface (optional)
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app/src
ENV MCP_DB_PATH=/app/azure_linux_images.db

# Default command runs the MCP server
CMD ["python3", "mcp_server.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.path.append('/app/src'); from database import ImageDatabase; db = ImageDatabase('/app/azure_linux_images.db'); stats = db.get_vulnerability_statistics(); db.close(); print('Health check passed')" || exit 1

# Labels for metadata
LABEL org.opencontainers.image.title="Container Image Recommendation MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for secure container base image recommendations"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="Container Security Team"
LABEL org.opencontainers.image.source="https://github.com/maniSbindra/secure-container-base-image-recommender"
LABEL org.opencontainers.image.documentation="https://github.com/maniSbindra/secure-container-base-image-recommender/blob/main/README.md"