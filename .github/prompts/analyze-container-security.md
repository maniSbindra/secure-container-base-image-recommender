# Analyze Existing Container Image Security

## Description
Analyze your current container image for security vulnerabilities and get recommendations for more secure alternatives.

## Prompt
I want to analyze my current container image for security vulnerabilities and get recommendations for more secure alternatives.

**Current Image:** [Specify your current container image, e.g., docker.io/library/python:3.12-slim, node:18-alpine, etc.]

Please help me:
1. Analyze the security posture of my current container image
2. Identify any known vulnerabilities (critical, high, medium, low)
3. Get recommendations for more secure alternative base images
4. Compare the security improvements of switching to recommended alternatives
5. Provide migration guidance if switching is recommended

If the image is not in your security database, please:
- Extract the programming language and version from the image name
- Provide secure alternatives based on the detected language
- Explain why the recommended alternatives are more secure

Use the MCP tools to perform comprehensive security analysis and provide actionable recommendations.

## Usage Example
"Please analyze the security of docker.io/library/python:3.12-slim and recommend more secure alternatives for my Python application."

## Expected Output
- Current image vulnerability analysis
- Security assessment and risk level
- List of more secure alternative images
- Security improvement metrics when switching
- Migration recommendations and considerations