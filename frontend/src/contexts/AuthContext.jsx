import { createContext, useContext, useState } from 'react'
import settings from '../settings'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(settings.tokenKey))
  const [user, setUser]   = useState(() => {
    const stored = localStorage.getItem(settings.userKey)
    return stored ? JSON.parse(stored) : null
  })

  function login(newToken, newUser) {
    localStorage.setItem(settings.tokenKey, newToken)
    localStorage.setItem(settings.userKey, JSON.stringify(newUser))
    setToken(newToken)
    setUser(newUser)
  }

  function logout() {
    localStorage.removeItem(settings.tokenKey)
    localStorage.removeItem(settings.userKey)
    setToken(null)
    setUser(null)
    window.location.replace('/login')
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
