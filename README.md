# Django API Boilerplate

A clean, production-ready Django REST API boilerplate with Docker support, PostgreSQL, Redis, and Celery for background tasks. Built with `uv` for fast dependency management.

## Features

- **Django 5.1** with Django REST Framework
- **uv** for fast Python package management
- **Docker & Docker Compose** for easy deployment
- **PostgreSQL** database with Redis for caching
- **Celery** for background task processing
- **Custom User Model** with email authentication
- **API-only** - no templates or HTML rendering
- **Simple API responses** and error handling
- **Health check endpoints** for monitoring
- **CORS support** for frontend integration

## Project Structure

```
django_api_project/
├── django_api_project/          # Main project settings
│   ├── settings.py              # Django settings
│   ├── urls.py                  # URL configuration
│   ├── wsgi.py                  # WSGI configuration
│   ├── asgi.py                  # ASGI configuration
│   └── celery.py                # Celery configuration
├── core/                        # Core utilities
│   ├── exceptions.py            # Exception handling
│   ├── responses.py             # Simple API responses
│   ├── views.py                 # Health check views
│   └── urls.py                  # Core URLs
├── accounts/                    # User management app
│   ├── models.py                # Custom User model
│   ├── serializers.py           # User serializers
│   ├── views.py                 # Authentication views
│   ├── urls.py                  # Account URLs
│   └── admin.py                 # Admin configuration
├── docker-compose.yml           # Docker services
├── Dockerfile                   # Docker configuration
├── pyproject.toml               # uv project configuration
├── Makefile                     # Development commands
└── manage.py                    # Django management
```

## Quick Start

### 1. Clone and Setup

```bash
# Copy environment file
cp env.example .env

# Edit .env with your settings
nano .env
```

### 2. Using Docker (Recommended)

```bash
# Build and start all services
make dev-setup

# Or manually:
make build
make up
make migrate
```

### 3. Create Superuser

```bash
make superuser
```

### 4. Access the API

- **API Base URL**: http://localhost:8000/api/v1/
- **Admin Panel**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/api/v1/health/

## API Endpoints

### Authentication
- `POST /api/v1/register/` - User registration
- `POST /api/v1/login/` - User login
- `POST /api/v1/logout/` - User logout
- `GET /api/v1/profile/` - Get user profile
- `PUT /api/v1/profile/` - Update user profile

### Health Checks
- `GET /api/v1/health/` - Basic health check
- `GET /api/v1/health/ready/` - Readiness check
- `GET /api/v1/health/live/` - Liveness check

### Available Tasks
- `send_welcome_email(user_id)` - Send welcome email to new users
- `process_user_data(user_id, data)` - Process user data in background

## Development Commands

```bash
# Start development environment
make dev-setup

# View logs
make logs

# Open Django shell
make shell

# Clean up
make clean
```

## Local Development (Without Docker)

```bash
# Install dependencies with uv
make install

# Set up environment variables
cp env.example .env

# Run migrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser

# Start development server
make run
```

## Environment Variables

Key environment variables in `.env`:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DB_NAME=django_api_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Adding New Apps

1. Create a new Django app:
   ```bash
   uv run python manage.py startapp your_app_name
   ```

2. Add to `INSTALLED_APPS` in `settings.py`

3. Create URLs and include in main `urls.py`

4. Follow the existing patterns for models, serializers, and views

## Package Management with uv

This project uses `uv` for fast Python package management:

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Sync dependencies
uv sync

# Run commands with uv
uv run python manage.py migrate
uv run python manage.py test
```

## Production Deployment

1. Set `DEBUG=False` in production
2. Use a proper secret key
3. Configure proper database credentials
4. Set up proper logging
5. Use a reverse proxy (nginx) in front of the application
6. Configure SSL/TLS certificates

## Contributing

1. Follow Django best practices
2. Use the existing code style and patterns
3. Update documentation as needed

## License

This project is open source and available under the MIT License.
