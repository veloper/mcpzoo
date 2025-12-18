import axios, { AxiosInstance } from 'axios'

const API_BASE_URL = '/api' // keep relative; nginx proxies /api to backend

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

    this.token = localStorage.getItem('access_token')
    if (this.token) {
      this.setAuthHeader()
    }

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

  async login(username: string, password: string) {
    const response = await this.client.post('/auth/login', { username, password })
    return response.data
  }

  async logout() {
    await this.client.post('/auth/logout')
    this.clearToken()
  }

  async listServers() {
    const response = await this.client.get('/servers')
    return response.data
  }

  async getServer(id: string) {
    const response = await this.client.get(`/servers/${id}`)
    return response.data
  }

  async createServer(server: any) {
    const response = await this.client.post('/servers', server)
    return response.data
  }

  async updateServer(id: string, server: any) {
    const response = await this.client.put(`/servers/${id}`, server)
    return response.data
  }

  async deleteServer(id: string) {
    await this.client.delete(`/servers/${id}`)
  }

  async syncServers() {
    const response = await this.client.post('/servers/sync')
    return response.data
  }

  async getServerLogs(serverId: string, type: 'stdout' | 'stderr' = 'stdout') {
    const response = await this.client.get(`/servers/${serverId}/logs`, { params: { type } })
    return response.data
  }

  async get(url: string, config?: any) {
    console.log('API Client GET:', url)
    try {
      const response = await this.client.get(url, config)
      console.log('API Client response:', response)
      console.log('API Client response.data:', response.data)
      console.log('API Client response.status:', response.status)
      console.log('API Client response headers:', response.headers)
      console.log('API Client raw response text:', response.request?.responseText)
      return response.data
    } catch (error: any) {
      console.error('API Client GET error:', error)
      console.error('API Client error response:', error.response)
      console.error('API Client error response data:', error.response?.data)
      throw error
    }
  }

  async post(url: string, data?: any, config?: any) {
    const response = await this.client.post(url, data, config)
    return response.data
  }

  async startServer(id: string) {
    const response = await this.client.post(`/servers/${id}/start`)
    return response.data
  }

  async stopServer(id: string) {
    const response = await this.client.post(`/servers/${id}/stop`)
    return response.data
  }

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
