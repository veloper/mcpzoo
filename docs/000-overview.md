# MCPZoo Project Overview

## Project Description
MCPZoo is a distributed process and server management system built with FastAPI (Python) backend and React (TypeScript) frontend. It provides real-time monitoring and control of multiple servers and their processes.

## Key Features
- Multi-server management and monitoring
- Real-time process supervision via Supervisor
- Web-based dashboard
- RESTful API
- Authentication and authorization
- Docker containerization
- Nginx reverse proxy

## Technology Stack
- **Backend**: Python 3.11, FastAPI, TinyDB, Supervisor
- **Frontend**: React 18, TypeScript, Vite
- **DevOps**: Docker, Docker Compose, Nginx, Supervisor
- **Database**: TinyDB (JSON-based)

## Project Structure
```
mcpzoo/
├── backend/                 # Python FastAPI application
│   ├── src/backend/        # Main application code
│   │   ├── main.py         # FastAPI app entry point
│   │   ├── settings.py     # Configuration
│   │   ├── models.py       # Pydantic models
│   │   ├── auth.py         # Authentication logic
│   │   ├── supervisor_api.py # Supervisor integration
│   │   ├── sync_processes.py # Process synchronization
│   │   ├── tinydb.py       # Database layer
│   │   ├── routers/        # API route handlers
│   │   └── utils/          # Utility functions
│   └── pyproject.toml      # Python dependencies
├── frontend/                # React TypeScript application
│   ├── src/
│   │   ├── main.tsx        # Entry point
│   │   ├── App.tsx         # Root component
│   │   ├── api/            # API client
│   │   ├── context/        # React context
│   │   ├── hooks/          # Custom hooks
│   │   ├── pages/          # Page components
│   │   ├── components/     # Reusable components
│   │   └── styles/         # CSS styles
│   ├── public/             # Static files
│   ├── package.json        # Node dependencies
│   └── vite.config.ts      # Vite configuration
├── docker/                  # Docker configuration
│   ├── supervisor/         # Supervisor configs
│   └── nginx/              # Nginx configs
└── docs/                    # Documentation
```

## Architecture Layers

### Backend Architecture
1. **API Layer** (routers/) - FastAPI route handlers
2. **Business Logic** (auth.py, supervisor_api.py, sync_processes.py)
3. **Data Layer** (tinydb.py, models.py)
4. **Integration** (settings.py)

### Frontend Architecture
1. **Pages** - Route-specific page components
2. **Components** - Reusable UI components
3. **Hooks** - Custom React hooks for logic
4. **Context** - State management (Auth)
5. **API Client** - HTTP communication layer

## Data Flow
1. Frontend sends HTTP requests to API
2. API authenticates requests
3. Business logic processes requests
4. Data persisted to TinyDB
5. Response sent to frontend
6. Frontend updates UI state
7. Real-time process monitoring via polling

## Deployment
- Containerized with Docker
- Nginx reverse proxy
- Supervisor manages Python and Nginx processes
- Docker Compose orchestrates containers

## Development Workflow
1. Backend development using FastAPI + Uvicorn
2. Frontend development using Vite dev server
3. Testing of API endpoints
4. Build Docker image
5. Deploy with Docker Compose
