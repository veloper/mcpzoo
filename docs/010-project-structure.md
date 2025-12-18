# MCPZoo Project Structure Documentation

## Directory Layout

### Root Directory
```
mcpzoo/
├── backend/              # Python FastAPI backend
├── frontend/             # React TypeScript frontend
├── docker/               # Docker configuration
├── docs/                 # Documentation
├── data/                 # Data storage (gitignored)
├── Dockerfile            # Container definition
├── docker-compose.yml    # Multi-container orchestration
├── Makefile              # Build and run commands
├── .env                  # Environment variables (gitignored)
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── specs.md              # Project specifications
└── TODOLIST.md           # This todo list
```

### Backend Structure
```
backend/
├── src/backend/          # Main application code
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry
│   ├── settings.py       # Configuration and env vars
│   ├── models.py         # Pydantic data models
│   ├── auth.py           # JWT authentication
│   ├── supervisor_api.py # Supervisor RPC integration
│   ├── sync_processes.py # Process sync logic
│   ├── tinydb.py         # Database wrapper
│   ├── routers/          # API route modules
│   │   ├── __init__.py
│   │   ├── auth.py       # Auth endpoints
│   │   ├── servers.py    # Server endpoints
│   │   └── processes.py  # Process endpoints
│   └── utils/            # Utility modules
│       ├── __init__.py
│       ├── shell.py      # Shell execution
│       └── logging.py    # Logging setup
├── tests/                # Test files
│   └── __init__.py
├── data/                 # Database files (gitignored)
│   └── database.json
├── pyproject.toml        # Python dependencies
└── .venv/                # Virtual environment
```

### Frontend Structure
```
frontend/
├── src/
│   ├── main.tsx          # Vite entry point
│   ├── App.tsx           # Root component
│   ├── api/              # API communication
│   │   └── client.ts     # API client class
│   ├── context/          # React context
│   │   └── AuthContext.tsx # Auth state
│   ├── hooks/            # Custom hooks
│   │   ├── useServers.ts # Servers data hook
│   │   └── useProcesses.ts # Processes data hook
│   ├── pages/            # Page components
│   │   ├── LoginPage.tsx
│   │   ├── HomePage.tsx
│   │   ├── ServersPage.tsx
│   │   └── ProcessesPage.tsx
│   ├── components/       # Reusable components
│   │   ├── Header.tsx
│   │   ├── LoginForm.tsx
│   │   ├── ServersList.tsx
│   │   ├── ServerForm.tsx
│   │   ├── ProcessesList.tsx
│   │   └── LogViewer.tsx
│   └── styles/           # Styling
│       └── style.css
├── public/               # Static assets
│   └── index.html
├── dist/                 # Built output
│   └── (built by Vite)
├── package.json          # Node dependencies
├── vite.config.ts        # Vite configuration
└── tsconfig.json         # TypeScript configuration
```

### Docker Configuration
```
docker/
├── supervisor/           # Supervisor configs
│   ├── supervisord.conf  # Main supervisor config
│   ├── mcp_group.conf    # Process group config
│   ├── backend.conf      # Backend process config
│   └── nginx.conf        # Nginx process config
└── nginx/                # Nginx configuration
    └── default.conf      # Nginx site config
```

## File Purposes

### Backend Core Files
- **main.py**: FastAPI app initialization, route registration
- **settings.py**: Environment variables, config classes
- **models.py**: Pydantic models for validation
- **auth.py**: JWT token generation and validation
- **supervisor_api.py**: RPC client for Supervisor
- **sync_processes.py**: Synchronization logic for process state
- **tinydb.py**: Database abstraction layer
- **routers/auth.py**: Login, logout endpoints
- **routers/servers.py**: Server CRUD operations
- **routers/processes.py**: Process control endpoints
- **utils/shell.py**: Shell command execution
- **utils/logging.py**: Logging configuration

### Frontend Core Files
- **main.tsx**: React root, Vite entry
- **App.tsx**: Router setup, main layout
- **api/client.ts**: Axios/Fetch API wrapper
- **context/AuthContext.tsx**: Global auth state
- **hooks/useServers.ts**: Fetch and cache servers
- **hooks/useProcesses.ts**: Fetch and cache processes
- **pages/***: Route-specific pages
- **components/***: Reusable UI elements
- **style.css**: Global styles and responsive design

### Configuration Files
- **backend/pyproject.toml**: Python package config
- **frontend/package.json**: Node package config
- **frontend/vite.config.ts**: Vite build config
- **docker-compose.yml**: Multi-container setup
- **Dockerfile**: Container image definition
- **Makefile**: Common commands
- **.env**: Runtime environment variables
- **.env.example**: Template for .env
- **.gitignore**: Git exclusions

## Key Design Patterns

### Backend
- **Router Pattern**: Modular endpoint organization
- **Dependency Injection**: Settings and database passed to routers
- **Factory Pattern**: Supervisor client creation
- **Singleton**: TinyDB database instance

### Frontend
- **Context API**: Global auth state
- **Custom Hooks**: Data fetching logic reusability
- **Component Composition**: Small, focused components
- **CSS Modules**: Scoped styling

## Data Storage

- **Primary**: TinyDB (JSON file in backend/data/)
- **Ephemeral**: React state in frontend
- **Config**: Environment variables (.env)
- **Logs**: Generated by Supervisor and processes

## Build Artifacts

- **Frontend**: dist/ directory (built by Vite)
- **Backend**: Compiled Python (in .venv/)
- **Docker**: Image layers from Dockerfile
