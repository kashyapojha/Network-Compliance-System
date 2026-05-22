import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const apiUrl = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? '' : 'http://localhost:5000')

  useEffect(() => {
    axios.defaults.baseURL = apiUrl
    axios.defaults.timeout = 10000 // 10 second timeout
    
    const token = localStorage.getItem('token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchCurrentUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get('/api/auth/me')
      setUser(response.data)
      setError(null)
    } catch (error) {
      console.error('Failed to fetch current user:', error)
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
      setError('Session expired. Please login again.')
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    try {
      setError(null)
      const response = await axios.post('/api/auth/login', { username, password })
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
