/**
 * Authentication client for Supabase auth operations.
 */

import { supabase } from './supabaseClient'
import { saveAccessToken, clearAccessToken, saveUser } from './authStorage'

export interface AuthUser {
  id: string
  email: string | null
  firstName?: string | null
  lastName?: string | null
  createdAt?: string | null
}

export interface AuthResponse {
  user: AuthUser | null
  error: string | null
}

/**
 * Sign up a new user with email and password.
 */
export async function signUp(
  email: string, 
  password: string, 
  firstName?: string, 
  lastName?: string
): Promise<AuthResponse> {
  try {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          first_name: firstName || '',
          last_name: lastName || '',
        }
      }
    })

    if (error) {
      return { user: null, error: error.message }
    }

    if (data.session && data.user) {
      await saveAccessToken(data.session.access_token)
      const userMetadata = data.user.user_metadata || {}
      const user: AuthUser = {
        id: data.user.id,
        email: data.user.email || null,
        firstName: userMetadata.first_name || null,
        lastName: userMetadata.last_name || null,
        createdAt: data.user.created_at || null,
      }
      saveUser(user)
      return { user, error: null }
    }

    // If no session (email confirmation required), still return user
    if (data.user) {
      const userMetadata = data.user.user_metadata || {}
      const user: AuthUser = {
        id: data.user.id,
        email: data.user.email || null,
        firstName: userMetadata.first_name || null,
        lastName: userMetadata.last_name || null,
        createdAt: data.user.created_at || null,
      }
      return { user, error: 'Please check your email to confirm your account' }
    }

    return { user: null, error: 'Sign up failed' }
  } catch (error: any) {
    return { user: null, error: error.message || 'Sign up failed' }
  }
}

/**
 * Sign in an existing user with email and password.
 */
export async function signIn(email: string, password: string): Promise<AuthResponse> {
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      return { user: null, error: error.message }
    }

    if (data.session && data.user) {
      await saveAccessToken(data.session.access_token)
      const userMetadata = data.user.user_metadata || {}
      const user: AuthUser = {
        id: data.user.id,
        email: data.user.email || null,
        firstName: userMetadata.first_name || null,
        lastName: userMetadata.last_name || null,
        createdAt: data.user.created_at || null,
      }
      saveUser(user)
      return { user, error: null }
    }

    return { user: null, error: 'Sign in failed' }
  } catch (error: any) {
    return { user: null, error: error.message || 'Sign in failed' }
  }
}

/**
 * Sign out the current user.
 */
export async function signOut(): Promise<void> {
  try {
    await supabase.auth.signOut()
  } catch (error) {
    console.error('Error signing out:', error)
  } finally {
    await clearAccessToken()
  }
}

