'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { getAccessToken, getUser, clearAccessToken, saveUser } from '@/lib/authStorage'
import { callRagardAPI } from '@/lib/api'
import { AuthUser } from '@/lib/authClient'

interface AuthContextType {
  isLoggedIn: boolean
  user: AuthUser | null
  loading: boolean
  setUser: (user: AuthUser | null) => void
  setIsLoggedIn: (isLoggedIn: boolean) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  // Check auth state on mount
  useEffect(() => {
    async function checkAuth() {
      try {
        const token = await getAccessToken()
        const storedUser = getUser()

        if (token && storedUser) {
          // Verify token is still valid by calling /api/me
          try {
            const meResponse = await callRagardAPI('/api/me', {
              method: 'GET',
            })

            if (meResponse && meResponse.id) {
              const currentUser = {
                id: meResponse.id,
                email: meResponse.email,
                firstName: meResponse.firstName || storedUser.firstName || null,
                lastName: meResponse.lastName || storedUser.lastName || null,
                createdAt: meResponse.createdAt || storedUser.createdAt || null,
              }
              setUser(currentUser)
              saveUser(currentUser)
              setIsLoggedIn(true)
            } else {
              // Invalid response, clear auth
              await clearAccessToken()
              setUser(null)
              setIsLoggedIn(false)
            }
          } catch (error) {
            // Token invalid or expired, but try to use stored user data
            if (storedUser) {
              setUser({
                id: storedUser.id,
                email: storedUser.email,
                firstName: storedUser.firstName || null,
                lastName: storedUser.lastName || null,
              })
              setIsLoggedIn(true)
            } else {
              await clearAccessToken()
              setUser(null)
              setIsLoggedIn(false)
            }
          }
        } else {
          setUser(null)
          setIsLoggedIn(false)
        }
      } catch (error) {
        console.error('Error checking auth:', error)
        setUser(null)
        setIsLoggedIn(false)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  return (
    <AuthContext.Provider value={{ isLoggedIn, user, loading, setUser, setIsLoggedIn }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

