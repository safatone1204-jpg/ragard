/**
 * Token storage utilities for authentication.
 * Uses localStorage for web app (Chrome extension would use chrome.storage).
 */

const TOKEN_STORAGE_KEY = 'ragardToken'
const USER_STORAGE_KEY = 'ragardUser'

export async function saveAccessToken(token: string): Promise<void> {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export async function getAccessToken(): Promise<string | null> {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export async function clearAccessToken(): Promise<void> {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(USER_STORAGE_KEY)
}

export function saveUser(user: { id: string; email: string | null; firstName?: string | null; lastName?: string | null }): void {
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
}

export function getUser(): { id: string; email: string | null; firstName?: string | null; lastName?: string | null } | null {
  const stored = localStorage.getItem(USER_STORAGE_KEY)
  if (!stored) return null
  try {
    return JSON.parse(stored)
  } catch {
    return null
  }
}

