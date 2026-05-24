import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

// FIX: Separate timeouts for different request types.
// The global 10s timeout was killing /api/auth/me on slow backend startups
// AND killing metrics fetches that run right after a scan.
// Rule: auth calls = 15s, scan calls = 60s, everything else = 15s.
// Never set axios.defaults.timeout — it affects ALL requests including scans.
const AUTH_TIMEOUT = 15000
const DEFAULT_TIMEOUT = 15000

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const apiUrl = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? '' : 'http://localhost:5000')

  // FIX: Add a global axios response interceptor that catches 401s anywhere
  // in the app (expired token mid-session) and clears auth state cleanly,
  // instead of each component handling it inconsistently or not at all.
  useEffect(() => {
    axios.defaults.baseURL = apiUrl
    // FIX: Removed axios.defaults.timeout — was killing scan + metrics requests

    const interceptor = axios.interceptors.response.use(
      response => response,
      error => {
        if (
          error.response?.status === 401 &&
          !error.config.url?.includes('/api/auth/login')
        ) {
          // Token expired or invalid mid-session — clear and redirect
          localStorage.removeItem('token')
          delete axios.defaults.headers.common['Authorization']
          setUser(null)
          setError('Session expired. Please login again.')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )

    const token = localStorage.getItem('token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchCurrentUser()
    } else {
      setLoading(false)
    }

    return () => axios.interceptors.response.eject(interceptor)
  }, [])

  const fetchCurrentUser = async () => {
    try {
      // FIX: explicit timeout on this call only — doesn't pollute global default
      const response = await axios.get('/api/auth/me', { timeout: AUTH_TIMEOUT })
      setUser(response.data)
      setError(null)
    } catch (error) {
      // FIX: Only clear token on definitive auth failures (401, 403).
      // Network errors and timeouts on startup should NOT log the user out —
      // the token may still be valid; the backend might just be starting up.
      if (error.response?.status === 401 || error.response?.status === 403) {
        localStorage.removeItem('token')
        delete axios.defaults.headers.common['Authorization']
        setError('Session expired. Please login again.')
      } else {
        // Timeout or network error — keep token, show a soft warning
        console.warn('Could not verify session (backend may be starting):', error.message)
        // Still set user as null so ProtectedRoute works correctly,
        // but don't destroy the token
        setUser(null)
      }
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    try {
      setError(null)
      const response = await axios.post(
        '/api/auth/login',
        { username, password },
        { timeout: AUTH_TIMEOUT }
      )
      const { access_token, user } = response.data
      localStorage.setItem('token', access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      setUser(user)
      return user
    } catch (error) {
      console.error('Login failed:', error)
      if (error.code === 'ECONNABORTED') {
        throw new Error('Request timeout. Please check your connection.')
      } else if (error.response?.status === 401) {
        throw new Error('Invalid username or password.')
      } else if (error.response?.status === 500) {
        throw new Error('Server error. Please try again later.')
      } else if (!error.response) {
        throw new Error('Network error. Please check if the backend is running.')
      } else {
        throw new Error(error.response?.data?.error || 'Login failed. Please try again.')
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
    setUser(null)
    setError(null)
    window.location.href = '/login'
  }

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    fetchCurrentUser
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}