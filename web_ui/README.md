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

### 📊 Analytics & Reporting
- Vulnerability distribution charts
- Language-based security statistics
- Size distribution analysis
- Export functionality for data backup

## Quick Start

### 1. Install Dependencies

```bash
cd web_ui
pip install -r requirements.txt
```

### 2. Start the Web Server

```bash
# Using the startup script (recommended)
./start.sh

# Or manually
python app.py
```

### 3. Access the Web Interface

Open your browser and navigate to: http://localhost:8080

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

### Viewing Analytics

1. Navigate to the **Analytics** page
2. Explore various charts and statistics:
   - Vulnerability distribution
   - Language-based security metrics
   - Image size distribution
3. Use insights to make informed decisions about base images

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

## Configuration

### Database Path
The web UI expects the SQLite database at `../azure_linux_images.db` relative to the web_ui directory. You can modify this in `app.py`:

```python
db_path = os.path.join(os.path.dirname(__file__), '..', 'your_database.db')
```

### Security
For production deployment:

1. Change the Flask secret key in `app.py`
2. Set `debug=False` in the Flask app configuration
3. Use a proper WSGI server like Gunicorn
4. Implement authentication if required
5. Use HTTPS in production

### Performance
For large databases:

1. Consider pagination limits in `app.py`
2. Implement database connection pooling
3. Add caching for frequently accessed data
4. Use asynchronous scanning for better user experience

## Troubleshooting

### Common Issues

1. **Database not found**
   - Ensure the SQLite database exists
   - Run a CLI scan first or use the web UI scan feature

2. **Import errors**
   - Make sure you're in the web_ui directory
   - Check that the src directory is accessible
   - Verify all dependencies are installed

3. **Scan failures**
   - Ensure Docker is running
   - Check internet connectivity
   - Verify sufficient disk space for temporary images

4. **Performance issues**
   - Reduce pagination size for large databases
   - Use filters to limit result sets
   - Consider running scans during off-peak hours

### Debug Mode

To enable debug mode, set the environment variable:

```bash
export FLASK_ENV=development
python app.py
```

## Development

### Adding New Features

1. Create new routes in `app.py`
2. Add corresponding templates in `templates/`
3. Update the navigation in `base.html`
4. Add any new database methods to `../src/database.py`

### Template Structure

- `base.html`: Base template with navigation and common styling
- `index.html`: Dashboard page
- `recommend.html`: Recommendation form and results
- `images.html`: Image listing and search
- `scan.html`: Registry scanning interface
- `error.html`: Error page template

### Styling

The UI uses Bootstrap 5 with custom CSS variables for Azure-themed styling. Main color scheme:

- Primary: Azure Blue (#0078d4)
- Secondary: Azure Light Blue (#40e0d0)
- Success: Security Green (#107c10)
- Warning: Orange (#ff8c00)
- Danger: Red (#d13438)

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "app.py"]
```

### Environment Variables

- `FLASK_ENV`: Set to 'production' for production
- `DATABASE_PATH`: Custom database path
- `SECRET_KEY`: Flask secret key for sessions

## Security Considerations

- The web UI provides access to container scanning capabilities
- Ensure proper network security when deploying
- Consider implementing authentication for production use
- Regularly update dependencies for security patches
- Monitor for unauthorized access attempts

## Support

For issues specific to the web UI:
1. Check the browser console for JavaScript errors
2. Review Flask logs for server-side issues
3. Verify database connectivity and permissions
4. Ensure all dependencies are properly installed

For general tool support, refer to the main README.md file.
