# Search Secure Container Images by Criteria

## Description
Search the security database for container images that meet specific security and functional requirements.

## Prompt
I need to search for container images that meet specific security and functional criteria. Please help me find images with the following requirements:

**Programming Language:** [Specify: python, nodejs, java, go, dotnet, etc.]
**Security Filter:** [Specify: zero_vulnerabilities, low_risk, medium_risk, or specific vulnerability threshold]
**Maximum Vulnerabilities:** [Specify number, e.g., 0 for zero vulnerabilities, 5 for low risk]
**Additional Criteria:** [Any other requirements like size, specific packages, base OS]

Please search the database and provide:
1. List of images matching the criteria
2. Detailed security information for each image
3. Language runtime versions available
4. Size and performance characteristics
5. Ranking by security score and overall suitability

Use the MCP search tools to query the security database effectively.

## Usage Examples
- "Find Python images with zero critical and high vulnerabilities"
- "Search for Node.js images with maximum 5 total vulnerabilities"
- "Find the most secure Java container images available"
- "Search for Go images with minimal security risks"

## Expected Output
- Filtered list of container images meeting criteria
- Security metrics for each image
- Comparison of options with recommendations
- Additional metadata like size, packages, and base OS information