# Container Security Migration Guide

## Description
Get guidance on migrating from your current container setup to more secure alternatives with step-by-step instructions.

## Prompt
I want to migrate my application to a more secure container base image. Please provide a comprehensive migration guide with the following details:

**Current Setup:**
- Current base image: [Specify your current image]
- Application type: [Web app, API, microservice, CLI tool, etc.]
- Programming language and version: [e.g., Python 3.12, Node.js 18]
- Key dependencies: [List important packages/frameworks]
- Deployment environment: [Docker, Kubernetes, cloud platform]

**Security Goals:**
- Target security level: [basic, high, maximum]
- Vulnerability tolerance: [zero, minimal, low]
- Compliance requirements: [If any, e.g., SOC2, HIPAA]

Please provide:
1. Analysis of current security posture
2. Recommended secure alternative base images
3. Step-by-step migration plan
4. Dockerfile changes needed
5. Testing and validation steps
6. Potential compatibility issues and solutions
7. Performance impact assessment

Use the MCP tools to analyze options and create a comprehensive migration strategy.

## Usage Example
"Help me migrate from ubuntu:20.04 to a more secure base image for my Python Flask API. I need high security with minimal vulnerabilities."

## Expected Output
- Current vs. recommended image comparison
- Detailed migration steps
- Updated Dockerfile examples
- Security improvement metrics
- Risk assessment and mitigation strategies