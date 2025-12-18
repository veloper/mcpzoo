# Phase 100: Frontend Setup and API Client

## Objective

Initialize Node dependencies and create the axios API client with authentication handling.

## Prerequisites

- Phase 030-038 (backend) completed
- Backend running successfully for API testing
- Node.js 20+ installed

## Steps

### 1.1: Initialize Node Dependencies

```bash
cd frontend
npm install
```

**Verify:**
```bash
npm list | head -20
# Should show react, react-dom, vite, typescript, etc.
```

---

### 1.2: Create API Client (src/api/client.ts)

Create `frontend/src/api/client.ts`:

```typescript
import axios, { AxiosInstance } from 'axios'

const API_BASE_URL = '/api'

class APIClient {
  private client: AxiosInstance
  private token: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Load token from localStorage
    this.token = localStorage.getItem('access_token')
    if (this.token) {
      this.setAuthHeader()
    }

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  private setAuthHeader() {
    if (this.token) {
      this.client.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
    }
  }

  setToken(token: string) {
    this.token = token
    localStorage.setItem('access_token', token)
    this.setAuthHeader()
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('access_token')
    delete this.client.defaults.headers.common['Authorization']
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const response = await this.client.post('/auth/login', { username, password })
    return response.data
  }

  async logout() {
    await this.client.post('/auth/logout')
    this.clearToken()
  }

  // Servers endpoints
  async listServers() {
    const response = await this.client.get('/servers')
    return response.data
  }

  async getServer(id: number) {
    const response = await this.client.get(`/servers/${id}`)
    return response.data
  }

  async createServer(server: any) {
    const response = await this.client.post('/servers', server)
    return response.data
  }

  async updateServer(id: number, server: any) {
    const response = await this.client.put(`/servers/${id}`, server)
    return response.data
  }

  async deleteServer(id: number) {
    await this.client.delete(`/servers/${id}`)
  }

  async syncServers() {
    const response = await this.client.post('/servers/sync')
    return response.data
  }

  async getServerLogs(serverId: number, type: 'stdout' | 'stderr' = 'stdout') {
    const response = await this.client.get(`/servers/${serverId}/logs`, { params: { type } })
    return response.data
  }

  // Generic methods for advanced usage
  async get(url: string, config?: any) {
    const response = await this.client.get(url, config)
    return response.data
  }

  async post(url: string, data?: any, config?: any) {
    const response = await this.client.post(url, data, config)
    return response.data
  }

  async startServer(id: number) {
    const response = await this.client.post(`/servers/${id}/start`)
    return response.data
  }

  async stopServer(id: number) {
    const response = await this.client.post(`/servers/${id}/stop`)
    return response.data
  }

  // Processes endpoints
  async listProcesses() {
    const response = await this.client.get('/processes')
    return response.data
  }

  async startProcess(name: string) {
    const response = await this.client.post(`/processes/${name}/start`)
    return response.data
  }

  async stopProcess(name: string) {
    const response = await this.client.post(`/processes/${name}/stop`)
    return response.data
  }
}

export const apiClient = new APIClient()
```

---

## Verification Checklist

- [ ] `npm install` completes without errors
- [ ] `frontend/src/api/client.ts` created
- [ ] APIClient class initializes correctly
- [ ] Authentication token storage works
- [ ] API endpoints are callable

## Next Step

Proceed to [101-auth-context-and-hooks.md](./101-auth-context-and-hooks.md)
