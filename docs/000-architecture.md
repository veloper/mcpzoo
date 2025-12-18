# MCPZoo Architecture Document

## System Architecture Overview

MCPZoo follows a client-server architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser                              │
│              (React TypeScript Frontend)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP/REST API
                     │
┌─────────────────────────────────────────────────────────────┐
│              Nginx Reverse Proxy                             │
│           (Port 80 → Backend 8000)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────────────┐
│            FastAPI Backend Application                       │
│                  (Python 3.11)                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Routes Layer (routers/)                             │   │
│  │  - /auth (authentication)                            │   │
│  │  - /servers (server management)                      │   │
│  │  - /processes (process management)                   │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Business Logic                                      │   │
│  │  - auth.py (JWT token validation)                    │   │
│  │  - supervisor_api.py (Supervisor RPC)               │   │
│  │  - sync_processes.py (Process synchronization)       │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Data Layer                                          │   │
│  │  - tinydb.py (JSON database)                         │   │
│  │  - models.py (Pydantic models)                       │   │
│  │  - settings.py (Configuration)                       │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   ┌────▼─────┐          ┌────────▼────┐
   │  TinyDB   │          │ Supervisor   │
   │  (JSON)   │          │ (RPC Port)   │
   └──────────┘          └──────────────┘
```

## Component Breakdown

### Frontend (React + TypeScript)
- **Entry**: main.tsx → App.tsx
- **Routing**: React Router v6
- **State**: AuthContext for global state
- **Pages**: Login, Home, Servers, Processes
- **Components**: Reusable UI widgets
- **Hooks**: useServers, useProcesses (data fetching)
- **Styling**: CSS with responsive design

### Backend (FastAPI)
- **Entry**: main.py (ASGI application)
- **Authentication**: JWT tokens in headers
- **Database**: TinyDB (single JSON file)
- **Integration**: Supervisor RPC client
- **Routers**: Modular endpoint definitions
- **Utilities**: Logging, shell commands

### Docker Infrastructure
- **Container Runtime**: Docker
- **Orchestration**: Docker Compose
- **Process Manager**: Supervisor (inside container)
- **Reverse Proxy**: Nginx
- **Entrypoint**: bash script for startup

## Data Models

### User
- username: string
- password_hash: string
- created_at: datetime

### Server
- id: string
- name: string
- host: string
- port: integer
- status: string (online/offline)
- created_at: datetime

### Process
- id: string
- server_id: string
- name: string
- status: string (running/stopped/crashed)
- pid: integer
- command: string
- created_at: datetime

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/verify` - Verify token

### Servers
- `GET /api/servers` - List all servers
- `POST /api/servers` - Create server
- `GET /api/servers/{id}` - Get server details
- `PUT /api/servers/{id}` - Update server
- `DELETE /api/servers/{id}` - Delete server

### Processes
- `GET /api/processes` - List all processes
- `GET /api/processes/{id}` - Get process details
- `POST /api/processes/{id}/start` - Start process
- `POST /api/processes/{id}/stop` - Stop process
- `POST /api/processes/{id}/restart` - Restart process
- `GET /api/processes/{id}/logs` - Get process logs

## Security Model

1. **Authentication**: JWT tokens generated on login
2. **Authorization**: Token validation on protected routes
3. **Storage**: Passwords hashed with bcrypt
4. **Communication**: HTTPS in production (via reverse proxy)

## Deployment Architecture

```
Docker Container
├── Supervisor (PID 1)
│   ├── Backend Process (Uvicorn)
│   └── Nginx Process
└── Data Volume
    └── database.json (TinyDB)
```

## Performance Considerations

1. **Caching**: Frontend caches API responses in state
2. **Polling**: Real-time updates via periodic API calls (5-10s intervals)
3. **Database**: TinyDB with in-memory operations
4. **Load**: Designed for small deployments (< 100 processes)

## Error Handling

1. **Frontend**: Try-catch with user feedback
2. **Backend**: Exception handlers with proper HTTP status codes
3. **Database**: File-based persistence ensures data durability
4. **Supervisor**: Monitors process health

## Future Enhancements

- WebSocket support for real-time updates
- Database migration to PostgreSQL
- Multi-user with role-based access control
- Process grouping and dependencies
- Metrics and alerting system
- Kubernetes deployment manifests
