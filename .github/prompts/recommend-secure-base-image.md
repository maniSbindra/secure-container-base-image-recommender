# Recommend Secure Container Base Image

## Description
Get recommendations for secure container base images based on your programming language and requirements.

## Prompt
I need a secure container base image recommendation. Please help me find the most secure base image for my application with the following requirements:

**Programming Language:** [Specify: python, nodejs, java, go, dotnet, etc.]
**Language Version:** [Specify version if known, e.g., 3.12, 18, 11, etc.]
**Required Packages:** [List any specific packages you need, e.g., flask, express, spring-boot]
**Size Preference:** [Specify: minimal, small, balanced, full]
**Security Level:** [Specify: basic, high, maximum]

Please provide:
1. Top 5 recommended secure base images ranked by security score
2. Vulnerability analysis for each recommendation
3. Size comparison and reasoning for each choice
4. Any specific security benefits of the recommended images

Use the MCP tools to analyze the current database of secure container images and provide actionable recommendations.

## Usage Example
"I need a secure container base image recommendation for a Python 3.12 application with flask and requests packages. I prefer minimal size with high security level."

## Expected Output
- Ranked list of secure base images
- Vulnerability counts (critical, high, medium, low)
- Size information and performance characteristics
- Security reasoning and recommendations