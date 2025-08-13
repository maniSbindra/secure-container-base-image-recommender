# Azure Linux Base Image Tool - Web UI

A user-friendly web interface for the Azure Linux Base Image Recommendation Tool, making it accessible to users who prefer a graphical interface over the command line.

## Features

### 🏠 Dashboard
- Overview of database statistics
- Quick access to key features
- Security metrics at a glance
- Language distribution summary

### 🔍 Image Recommendation
- Interactive form for specifying requirements
- Real-time recommendations with scoring
- Detailed reasoning for each recommendation
- Copy Docker commands with one click

### 📋 Image Browser
- Paginated list of all scanned images
- Filter by language and security level
- Search functionality
- Detailed view for each image

### 🔄 Registry Scanner
- Web-based interface for scanning Microsoft Container Registry
- Progress tracking and status updates
- Configurable scan options
- Automatic cleanup of temporary Docker images


## Usage Guide

### Getting Recommendations

1. Navigate to the **Recommend** page
2. Fill out the requirements form:
   - Select your programming language
   - Specify version requirements (optional)
   - List required packages (optional)
   - Choose size preference
   - Set security level
3. Click "Get Recommendations"
4. Review the ranked recommendations with detailed scoring
5. Copy Docker commands or view detailed image information

### Browsing Images

1. Navigate to the **Images** page
2. Use filters to narrow down results:
   - Language filter
   - Security filter (secure/safe/vulnerable/all)
3. Click on any image for detailed information
4. Use pagination to browse through all images

### Scanning the Registry

1. Navigate to the **Scan Registry** page
2. Configure scan options:
   - Enable comprehensive scan for detailed security analysis
   - Choose to update existing images
   - Set maximum tags per repository
3. Click "Start Scan" and monitor progress
4. View results and updated statistics

## API Endpoints

The web UI exposes several API endpoints for programmatic access:

### GET /api/stats
Returns database statistics and language summary.

### POST /api/recommend
Accepts recommendation requirements and returns ranked suggestions.

**Request Body:**
```json
{
  "language": "python",
  "version": "3.12",
  "packages": ["flask", "pandas"],
  "size_preference": "balanced",
  "security_level": "high",
  "max_vulnerabilities": 10,
  "max_critical_vulnerabilities": 0,
  "max_high_vulnerabilities": 0
}
```

### POST /api/scan
Triggers a registry scan with specified options.

**Request Body:**
```json
{
  "comprehensive": true,
  "update_existing": false,
  "max_tags": 5
}
```

### GET /api/search
Search images by name or other criteria.

**Query Parameters:**
- `q`: Search query
- `language`: Language filter
