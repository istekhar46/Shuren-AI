# Shuren Backend API

FastAPI-based backend service for the Shuren AI fitness application.

## Quick Start

For first-time setup, follow these steps:

1. **Install Prerequisites**: Python 3.11+, PostgreSQL 15+, Poetry
2. **Clone and Navigate**: `cd shuren/backend`
3. **Run Setup Script**:
   - Linux/macOS: `chmod +x run_local.sh && ./run_local.sh`
   - Windows: `run_local.bat`
4. **Configure `.env`**: Update database credentials and API keys when prompted
5. **Access API**: http://localhost:8000/api/docs

For detailed instructions, see [Setup Instructions](#setup-instructions) below.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 15 or higher
- Redis 7.0+ (optional, for caching)
- Poetry (Python dependency management)

## Technology Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15+ with asyncpg driver
- **ORM**: SQLAlchemy 2.0+ (async)
- **Validation**: Pydantic 2.0+
- **Authentication**: JWT (python-jose), Google OAuth2
- **Password Hashing**: bcrypt
- **Migrations**: Alembic
- **ASGI Server**: Uvicorn

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/      # REST API endpoints
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic validation schemas
│   ├── services/               # Business logic services
│   ├── core/                   # Security, config, dependencies
│   └── db/                     # Database session and migrations
├── tests/                      # Test suite
├── alembic/                    # Database migrations
├── requirements.txt            # Python dependencies
├── .env.example                # Environment configuration template
└── README.md                   # This file
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd shuren/backend
```

### 2. Install Poetry (if not already installed)

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Verify installation
poetry --version
```

### 3. Install Dependencies

```bash
# Install all dependencies (including dev dependencies)
poetry install --no-root

# Install only production dependencies
poetry install --no-root --without dev

# Activate the virtual environment
poetry shell
```

**Note**: The `--no-root` flag is used because this is an application (not a library), and we don't need to install it as a package.

### 4. Configure Environment Variables

```bash
# Copy the example environment file
copy .env.example .env  # Windows
# OR
cp .env.example .env    # macOS/Linux

# Edit .env and update the following required variables:
```

**Required Environment Variables:**

- `DATABASE_URL`: PostgreSQL connection string
  - Format: `postgresql+asyncpg://username:password@localhost:5432/database_name`
  - Example: `postgresql+asyncpg://shuren_user:your_password@localhost:5432/shuren_db`

- `JWT_SECRET_KEY`: Secure random key for JWT token signing
  - Generate using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

- `GOOGLE_CLIENT_ID`: Your Google OAuth 2.0 client ID
  - Obtain from [Google Cloud Console](https://console.cloud.google.com/)

- `GOOGLE_CLIENT_SECRET`: Your Google OAuth 2.0 client secret
  - Obtain from [Google Cloud Console](https://console.cloud.google.com/)

**Example .env file:**

```env
# Application
APP_NAME=Shuren Backend
DEBUG=True

# Database
DATABASE_URL=postgresql+asyncpg://shuren_user:your_password@localhost:5432/shuren_db

# JWT Authentication
JWT_SECRET_KEY=your-generated-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 5. Set Up PostgreSQL Database

```bash
# Create database (using psql or your preferred tool)
createdb shuren_db

# Or using psql
psql -U postgres
CREATE DATABASE shuren_db;
CREATE USER shuren_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE shuren_db TO shuren_user;
\q
```

### 6. Run Database Migrations

```bash
# Apply all migrations to set up the database schema
poetry run alembic upgrade head

# Note: Initial migration already exists in alembic/versions/
# Only create new migrations if you modify the models
```

### 7. Run the Development Server

**Option 1: Quick Start Script (Recommended)**

```bash
# Linux/macOS
chmod +x run_local.sh
./run_local.sh

# Windows
run_local.bat
```

The startup script will:
- Install dependencies
- Run database migrations
- Start the development server with auto-reload

**Option 2: Manual Start**

```bash
# Start the server with auto-reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**The API will be available at:**
- API: http://localhost:8000
- Interactive docs (Swagger UI): http://localhost:8000/api/docs
- Alternative docs (ReDoc): http://localhost:8000/api/redoc

## Running Tests

The project includes comprehensive unit tests and property-based tests to ensure correctness.

```bash
# Run all tests
poetry run pytest

# Run with coverage report (generates HTML report in htmlcov/)
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_auth_endpoints.py

# Run tests in verbose mode
poetry run pytest -v

# Run tests matching a pattern
poetry run pytest -k "test_auth"

# View coverage report
# Open htmlcov/index.html in your browser after running coverage
```

**Test Organization:**

- `tests/test_auth_endpoints.py` - Authentication endpoint tests
- `tests/test_onboarding_endpoints.py` - Onboarding flow tests
- `tests/test_profile_service.py` - Profile management tests
- `tests/test_data_validation_properties.py` - Property-based validation tests
- `tests/test_data_privacy_properties.py` - Privacy and soft-delete tests
- `tests/conftest.py` - Shared test fixtures and configuration

## Database Migrations

```bash
# Create a new migration after model changes
poetry run alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history

# View current migration version
poetry run alembic current
```

## API Documentation

Once the server is running, you can explore and test the API using the interactive documentation:

- **Swagger UI** (recommended): http://localhost:8000/api/docs
  - Interactive API explorer with "Try it out" functionality
  - Test endpoints directly from the browser
  - View request/response schemas
  
- **ReDoc**: http://localhost:8000/api/redoc
  - Alternative documentation with a clean, readable layout
  - Better for reading and understanding the API structure

Both documentation interfaces are automatically generated from the FastAPI application and are always up-to-date with the code.

## Development Commands

### Quick Start Scripts

The project includes startup scripts for easy local development:

**Linux/macOS:**
```bash
chmod +x run_local.sh
./run_local.sh
```

**Windows:**
```bash
run_local.bat
```

These scripts automatically:
1. Check for `.env` file (creates from `.env.example` if missing)
2. Install all dependencies via Poetry
3. Run database migrations
4. Start the development server with auto-reload

### Start Development Server

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run with Multiple Workers (Production)

```bash
poetry run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Add New Dependencies

```bash
# Add production dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Show installed packages
poetry show

# Reinstall all dependencies
poetry install --no-root --sync
```

### Format Code

```bash
# Install formatting tools
poetry add --group dev black isort

# Format code
poetry run black app/ tests/
poetry run isort app/ tests/
```

### Lint Code

```bash
# Install linting tools
poetry add --group dev flake8 mypy

# Run linters
poetry run flake8 app/ tests/
poetry run mypy app/
```

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `APP_NAME` | Application name | No | Shuren Backend |
| `DEBUG` | Enable debug mode | No | False |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Yes | - |
| `JWT_ALGORITHM` | JWT signing algorithm | No | HS256 |
| `JWT_ACCESS_TOKEN_EXPIRE_HOURS` | Token expiration time | No | 24 |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Yes | - |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Yes | - |
| `REDIS_URL` | Redis connection string | No | - |
| `CORS_ORIGINS` | Allowed CORS origins | No | - |
| `LOG_LEVEL` | Logging level | No | INFO |

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user with email/password
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/google` - Authenticate with Google OAuth
- `GET /api/v1/auth/me` - Get current user information

### Onboarding

- `GET /api/v1/onboarding/state` - Get current onboarding state
- `POST /api/v1/onboarding/step` - Submit onboarding step data
- `POST /api/v1/onboarding/complete` - Complete onboarding and create profile

### Profiles

- `GET /api/v1/profiles/me` - Get user profile with all preferences
- `PATCH /api/v1/profiles/me` - Update user profile
- `POST /api/v1/profiles/me/lock` - Lock user profile

## Performance Targets

- User profile query: < 100ms
- Onboarding state load: < 200ms
- Authentication: < 150ms

## Troubleshooting

### Poetry Installation Errors

If you see "The current project could not be installed" error:

```bash
# Use --no-root flag (this is an application, not a library)
poetry install --no-root

# Or reinstall with sync
poetry install --no-root --sync
```

This is expected because `package-mode = false` is set in `pyproject.toml` for application projects.

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U shuren_user -d shuren_db -h localhost

# Check if PostgreSQL is running
# Windows: Check Services
# Linux/macOS: systemctl status postgresql
```

### Migration Issues

```bash
# Reset database (WARNING: destroys all data)
alembic downgrade base
alembic upgrade head

# Or drop and recreate database
dropdb shuren_db
createdb shuren_db
alembic upgrade head
```

### Import Errors

```bash
# Ensure Poetry environment is activated
poetry shell

# Reinstall dependencies
poetry install --sync
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Ensure all tests pass
5. Submit a pull request

## License

[License information]

## Support

For issues and questions, please contact [support contact].
