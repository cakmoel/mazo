# Mazo - Production Load Testing Suite

Mazo is a comprehensive, production-ready load testing suite built with Locust for PHP MVC web applications. It simulates realistic user behavior with both authenticated (admin) and anonymous (reader) user scenarios.

## Features

- **Realistic User Simulation**: Models both admin and reader user behavior with proper authentication
- **Dynamic Route Loading**: Automatically loads application routes from JSON configuration
- **Enhanced Error Handling**: Comprehensive error detection and reporting
- **Flexible Configuration**: Customizable test parameters via command-line options
- **Production Ready**: Built for enterprise-level load testing with monitoring and logging

## Prerequisites

- **Python 3.7+** - Required runtime environment
- **Target Application** - PHP MVC application accessible via HTTP
- **Route Configuration** - `routes.json` file (generated from your application)

## Installation

### Quick Start

1. **Clone or download this project:**
   ```bash
   git clone https://github.com/cakmoel/mazo.git
   cd mazo
   ```

2. **Run the automated setup script:**
   ```bash
   ./locust.sh --check-only
   ```

   This will:
   - Check for Python 3 installation
   - Create a virtual environment
   - Install required dependencies
   - Validate configuration files

### Manual Installation

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r loadrequirements.txt
   ```

## Configuration

### Route Setup

The most important prerequisite is having a `routes.json` file that defines your application's URL structure. This file should be exported from your PHP MVC application and contain route definitions like:

```json
{
  "home": {
    "urls": ["/", "/home"],
    "methods": ["GET"],
    "controller": "HomeController@index"
  },
  "single": {
    "urls": ["/post/1/hello-world", "/post/2/another-post"],
    "methods": ["GET"],
    "controller": "PostController@show"
  }
}
```

### User Credentials

The suite comes with pre-configured test users. Update these in `locustfile.py`:

- **Admin Users**: Default usernames and passwords for administrative operations
- **Reader Users**: Regular user accounts for public content access

## Usage

### Basic Load Testing

1. **Start the web interface:**
   ```bash
   ./locust.sh --host http://your-app-url.com
   ```

2. **Open your browser** to `http://localhost:8089`

3. **Configure your test** in the web interface:
   - Number of users to simulate
   - Spawn rate (users per second)
   - Host target (pre-filled)

4. **Start the test** and monitor real-time statistics

### Advanced Usage

#### Command Line Options

```bash
# Target a staging environment
./locust.sh --host https://staging.example.com --users 100 --spawn-rate 10

# Run only specific test types
./locust.sh --tags admin --port 9090

# Exclude admin operations
./locust.sh --exclude-tags admin --users 200

# Headless mode (no web interface)
./locust.sh --host https://prod.example.com --users 500 --spawn-rate 20 --headless
```

#### Test Tags

- `browse` - General content browsing (homepage, posts, categories)
- `public` - Public access operations
- `admin` - Administrative dashboard and management
- `interactive` - User interactions (comments, forms)
- `search` - Search functionality
- `feed` - RSS and sitemap access

### User Scenarios

#### Reader Users (80% weight)
- Browse homepage and blog posts
- View categories and archives
- Search content
- Submit comments
- Access RSS feeds and sitemaps

#### Admin Users (20% weight)
- Automatic login with credentials
- Access dashboard
- Manage posts, comments, users, categories
- Create new content
- Profile management

## Monitoring

The Locust web interface provides real-time metrics:

- **Requests per second**
- **Response times**
- **Failure rates**
- **Active users**
- **Performance breakdown by endpoint`

## File Structure

```
mazo/
├── locustfile.py          # Main Locust test configuration
├── locust.sh              # Automated setup and execution script
├── loadrequirements.txt   # Python dependencies
├── routes.json           # Application route definitions
└── README.md            # This documentation
```

## Best Practices

1. **Start Small**: Begin with low user counts and gradually increase
2. **Monitor Your Target**: Watch server metrics during tests
3. **Use Tags**: Focus on specific functionality with tag filtering
4. **Test Different Scenarios**: Mix of admin and public user patterns
5. **Check Routes**: Ensure `routes.json` matches your application

## Troubleshooting

### Common Issues

- **"Route file not found"**: Generate `routes.json` from your PHP application
- **"Connection refused"**: Verify target host is accessible
- **"Authentication failed"**: Check user credentials match target system
- **"High memory usage"**: Reduce user count or increase system resources

### Debug Mode

Run with detailed logging:
```bash
locust -f locustfile.py --host=http://target.com --loglevel DEBUG
```

## License

MIT License - see LICENSE file for details.

## Author

M. Noermoehammad - [GitHub](https://github.com/cakmoel)

---

For production deployments, consider running the Locust master server on a separate machine and connecting multiple worker nodes for distributed load testing.