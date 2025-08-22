# Clinic Management FastAPI Backend

A FastAPI backend application for clinic management with MySQL database integration.

## Project Structure

```
elfatih_backend/
├── api/                    # API route handlers
│   ├── __init__.py
│   └── users.py           # User-related endpoints
├── app/                   # Application package
├── crud/                  # CRUD operations
│   ├── __init__.py
│   └── user.py           # User CRUD operations
├── db/                    # Database configuration
│   ├── __init__.py
│   └── database.py       # Database setup and connection
├── models/                # SQLAlchemy models
│   ├── __init__.py
│   └── user.py           # User model
├── schemas/               # Pydantic schemas
│   ├── __init__.py
│   └── user.py           # User schemas
├── config.py             # Configuration settings
├── main.py               # FastAPI application entry point
├── run_server.py         # Server startup script
└── requirements.txt      # Python dependencies
```

## Database Configuration

The application connects to MySQL using the following connection string:
```
mysql+mysqlconnector://elfatih_user:123456@173.212.251.191:3306/elfatih_backend
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Option 1: Using main.py
```bash
python main.py
```

### Option 2: Using run_server.py
```bash
python run_server.py
```

### Option 3: Using uvicorn directly
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Users
- `POST /api/v1/users/` - Create a new user
- `GET /api/v1/users/` - Get all users (with pagination)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **MySQL Integration**: Using SQLAlchemy ORM with MySQL connector
- **CRUD Operations**: Complete Create, Read, Update, Delete operations
- **Data Validation**: Pydantic schemas for request/response validation
- **Auto Documentation**: Swagger UI and ReDoc integration
- **CORS Support**: Cross-Origin Resource Sharing enabled
- **Database Migration**: Automatic table creation on startup

## Development

The project is structured following FastAPI best practices:
- Separation of concerns with dedicated folders for different components
- Dependency injection for database sessions and CRUD operations
- Proper error handling with HTTP status codes
- Type hints throughout the codebase
