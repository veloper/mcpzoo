# Phase 106: Pages and Routing

## Objective

Implement page components and React Router for navigation.

## Prerequisites

- Phase 105 completed
- All components functional

## Steps

### 1.1: Create Home Page (src/pages/HomePage.tsx)

Create `frontend/src/pages/HomePage.tsx`:

```typescript
import React from 'react'
import { Header } from '../components/Header'
import { useServers } from '../hooks/useServers'
import { useProcesses } from '../hooks/useProcesses'

export function HomePage() {
  const { servers, loading: serversLoading } = useServers()
  const { processes, loading: processesLoading } = useProcesses()

  const runningProcesses = processes.filter(p => p.status === 'RUNNING').length
  const totalServers = servers.length

  return (
    <div className="page home-page">
      <Header />
      <main className="main-content">
        <section className="hero">
          <h2>Welcome to MCPZoo</h2>
          <p>Manage your MCP servers with ease</p>
        </section>

        <section className="dashboard-stats">
          <div className="stat-card">
            <div className="stat-number">{totalServers}</div>
            <div className="stat-label">Server Configurations</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{runningProcesses}</div>
            <div className="stat-label">Running Processes</div>
          </div>
        </section>

        <section className="quick-actions">
          <h3>Quick Actions</h3>
          <div className="action-buttons">
            <a href="/servers" className="btn-primary">Manage Servers</a>
            <a href="/processes" className="btn-secondary">View Processes</a>
          </div>
        </section>
      </main>
    </div>
  )
}
```

### 1.2: Create Servers Page (src/pages/ServersPage.tsx)

Create `frontend/src/pages/ServersPage.tsx`:

```typescript
import React from 'react'
import { Header } from '../components/Header'
import { ServersList } from '../components/ServersList'

export function ServersPage() {
  return (
    <div className="page servers-page">
      <Header />
      <main className="main-content">
        <ServersList />
      </main>
    </div>
  )
}
```

### 1.3: Create Processes Page (src/pages/ProcessesPage.tsx)

Create `frontend/src/pages/ProcessesPage.tsx`:

```typescript
import React from 'react'
import { Header } from '../components/Header'
import { ProcessesList } from '../components/ProcessesList'

export function ProcessesPage() {
  return (
    <div className="page processes-page">
      <Header />
      <main className="main-content">
        <ProcessesList />
      </main>
    </div>
  )
}
```

### 1.4: Create Login Page (src/pages/LoginPage.tsx)

Create `frontend/src/pages/LoginPage.tsx`:

```typescript
import React from 'react'
import { LoginForm } from '../components/LoginForm'

export function LoginPage() {
  return (
    <div className="page login-page">
      <LoginForm />
    </div>
  )
}
```

### 1.5: Update App.tsx with React Router (src/App.tsx)

Create `frontend/src/App.tsx`:

```typescript
import React from 'react'
import { BrowserRouter, Routes, Route, useLocation, Link, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { ServersPage } from './pages/ServersPage'
import { ProcessesPage } from './pages/ProcessesPage'

function Breadcrumbs() {
  const location = useLocation()
  
  const getBreadcrumbs = () => {
    const paths = location.pathname.split('/').filter(Boolean)
    
    const breadcrumbMap: Record<string, string> = {
      'servers': 'Servers',
      'processes': 'Processes',
    }
    
    const breadcrumbs = [
      { label: 'Home', path: '/' },
      ...paths.map((path, idx) => ({
        label: breadcrumbMap[path] || path,
        path: '/' + paths.slice(0, idx + 1).join('/'),
      })),
    ]
    
    return breadcrumbs
  }
  
  if (location.pathname === '/login') return null
  
  const breadcrumbs = getBreadcrumbs()
  
  return (
    <nav className="breadcrumbs">
      {breadcrumbs.map((crumb, idx) => (
        <React.Fragment key={crumb.path}>
          {idx > 0 && <span className="separator">/</span>}
          {idx === breadcrumbs.length - 1 ? (
            <span className="current">{crumb.label}</span>
          ) : (
            <Link to={crumb.path}>{crumb.label}</Link>
          )}
        </React.Fragment>
      ))}
    </nav>
  )
}

function AppContent() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <>
      <Breadcrumbs />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/servers" element={<ServersPage />} />
        <Route path="/processes" element={<ProcessesPage />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}
```

### 1.6: Create Frontend Entry Point (src/main.tsx)

Create `frontend/src/main.tsx`:

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import './styles/style.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>,
)
```

---

## Verification Checklist

- [ ] All page components created
- [ ] React Router configured
- [ ] Navigation between pages works
- [ ] Breadcrumbs display correctly
- [ ] AuthProvider wraps App
- [ ] Login page shows when not authenticated
- [ ] Protected pages work when authenticated

## Next Step

Proceed to [107-styling.md](./107-styling.md)
