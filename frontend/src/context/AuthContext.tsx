import React, { createContext, useState, useEffect } from 'react'
import { apiClient } from '../api/client'

interface AuthContextType {
  isAuthenticated: boolean
  username: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [username, setUsername] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      setIsAuthenticated(true)
      setUsername('user')
    }
    setLoading(false)
  }, [])

  const login = async (user: string, password: string) => {
    const response = await apiClient.login(user, password)
    apiClient.setToken(response.access_token)
    setIsAuthenticated(true)
    setUsername(user)
  }

  const logout = async () => {
    await apiClient.logout()
    setIsAuthenticated(false)
    setUsername(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, username, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export { AuthContext }
