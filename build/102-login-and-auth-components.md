# Phase 102: Login and Auth Components

## Objective

Implement the login form component and authentication UI.

## Prerequisites

- Phase 101 completed
- Auth context functional

## Steps

### 1.1: Create Login Component (src/components/LoginForm.tsx)

Create `frontend/src/components/LoginForm.tsx`:

```typescript
import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export function LoginForm() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(username, password)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h1>MCPZoo Login</h1>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  )
}
```

---

## Verification Checklist

- [ ] `frontend/src/components/LoginForm.tsx` created
- [ ] Login form displays correctly
- [ ] Form submission works
- [ ] Error messages display on failed login
- [ ] Loading state works

## Next Step

Proceed to [103-server-components.md](./103-server-components.md)
