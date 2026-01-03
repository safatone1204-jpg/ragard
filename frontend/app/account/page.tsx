'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { signIn, signUp, signOut } from '@/lib/authClient'
import { callRagardAPI, fetchUserRegard, uploadTradeHistory, getUploadProgress, fetchSavedAnalyses, downloadUserReport, type UserRegardResponse, type SavedAnalysis, type UploadProgress } from '@/lib/api'
import { fetchWatchlists, getWatchlistItems, type Watchlist } from '@/lib/watchlistAPI'
import Card from '@/components/Card'
import RagardScoreGauge from '@/components/RagardScoreGauge'
import RadarLoader from '@/components/RadarLoader'

type AuthMode = 'login' | 'signup'

export default function AccountPage() {
  const { isLoggedIn, user, setUser, setIsLoggedIn, loading } = useAuth()
  const router = useRouter()
  const [mode, setMode] = useState<AuthMode>('login')
  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [authLoading, setAuthLoading] = useState(false)

  // User Regard Score state
  const [userRegard, setUserRegard] = useState<UserRegardResponse | null>(null)
  const [regardLoading, setRegardLoading] = useState(false)

  // Trade History upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState<string>('')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null)
  const [progressPolling, setProgressPolling] = useState<NodeJS.Timeout | null>(null)
  
  // Report download state
  const [downloadingReport, setDownloadingReport] = useState(false)

  // Activity state
  const [watchlists, setWatchlists] = useState<Watchlist[]>([])
  const [totalTickers, setTotalTickers] = useState(0)
  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>([])
  const [activityLoading, setActivityLoading] = useState(false)

  // Settings state
  const [defaultTimeframe, setDefaultTimeframe] = useState<'24h' | '7d' | '30d'>('24h')
  const [riskProfile, setRiskProfile] = useState<'conservative' | 'balanced' | 'degen'>('balanced')

  // Listen for unauthorized events
  useEffect(() => {
    const handleUnauthorized = () => {
      setIsLoggedIn(false)
      setUser(null)
    }

    window.addEventListener('auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [setIsLoggedIn, setUser])

  // Load user regard score when logged in
  useEffect(() => {
    if (!isLoggedIn) {
      setUserRegard(null)
      return
    }

    async function loadUserRegard() {
      try {
        setRegardLoading(true)
        const data = await fetchUserRegard()
        setUserRegard(data)
      } catch (err: any) {
        // Endpoint might not exist yet - that's okay
        console.log('User regard endpoint not available:', err)
        setUserRegard(null)
      } finally {
        setRegardLoading(false)
      }
    }

    loadUserRegard()
  }, [isLoggedIn])

  // Load activity data when logged in
  useEffect(() => {
    if (!isLoggedIn) {
      setWatchlists([])
      setSavedAnalyses([])
      setTotalTickers(0)
      return
    }

    async function loadActivity() {
      try {
        setActivityLoading(true)
        
        // Load watchlists
        try {
          const watchlistsData = await fetchWatchlists()
          setWatchlists(watchlistsData)
          
          // Count total tickers across all watchlists
          let tickerCount = 0
          for (const wl of watchlistsData) {
            try {
              const items = await getWatchlistItems(wl.id)
              tickerCount += items.length
            } catch {
              // Skip if items can't be loaded
            }
          }
          setTotalTickers(tickerCount)
        } catch (err) {
          console.log('Could not load watchlists:', err)
        }

        // Load saved analyses
        try {
          const analyses = await fetchSavedAnalyses(3)
          setSavedAnalyses(analyses)
        } catch (err) {
          console.log('Could not load saved analyses:', err)
        }
      } finally {
        setActivityLoading(false)
      }
    }

    loadActivity()
  }, [isLoggedIn])

  // Load settings from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedTimeframe = localStorage.getItem('ragard_default_timeframe')
      const savedRiskProfile = localStorage.getItem('ragard_risk_profile')
      
      if (savedTimeframe && ['24h', '7d', '30d'].includes(savedTimeframe)) {
        setDefaultTimeframe(savedTimeframe as '24h' | '7d' | '30d')
      }
      if (savedRiskProfile && ['conservative', 'balanced', 'degen'].includes(savedRiskProfile)) {
        setRiskProfile(savedRiskProfile as 'conservative' | 'balanced' | 'degen')
      }
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (mode === 'signup' && password !== passwordConfirm) {
      setError('Passwords do not match')
      return
    }

    setAuthLoading(true)

    try {
      let response
      if (mode === 'login') {
        response = await signIn(email, password)
      } else {
        response = await signUp(email, password, firstName, lastName)
      }

      if (response.error) {
        setError(response.error)
        return
      }

      if (response.user) {
        setUser({
          id: response.user.id,
          email: response.user.email,
          firstName: response.user.firstName,
          lastName: response.user.lastName,
        })
        setIsLoggedIn(true)
        
        try {
          const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Verification timeout')), 5000)
          )
          
          const meResponse = await Promise.race([
            callRagardAPI('/api/me', { method: 'GET' }),
            timeoutPromise
          ]) as any
          
          if (meResponse && meResponse.id) {
            setUser({
              id: meResponse.id,
              email: meResponse.email,
              firstName: meResponse.firstName,
              lastName: meResponse.lastName,
            })
          }
        } catch (err: any) {
          console.warn('Backend verification failed, but user is logged in:', err)
        }
        
        setSuccess(mode === 'login' ? 'Logged in successfully!' : 'Account created! Please check your email to confirm.')
        setEmail('')
        setFirstName('')
        setLastName('')
        setPassword('')
        setPasswordConfirm('')
      } else {
        setError('Login failed - no user data received')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
      console.error('Login error:', err)
    } finally {
      setAuthLoading(false)
    }
  }

  const handleSignOut = async () => {
    setAuthLoading(true)
    try {
      await signOut()
      setUser(null)
      setIsLoggedIn(false)
      setSuccess('Logged out successfully')
      setUserRegard(null)
      setWatchlists([])
      setSavedAnalyses([])
    } catch (err: any) {
      setError(err.message || 'Failed to log out')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setUploadStatus('')
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus('Please select a file first.')
      return
    }

    setUploading(true)
    setUploadStatus('Uploading...')
    setUploadProgress(null)

    // Clear any existing polling
    if (progressPolling) {
      clearTimeout(progressPolling)
      setProgressPolling(null)
    }

    // Start polling for progress
    let shouldContinuePolling = true
    
    const pollProgress = async () => {
      if (!shouldContinuePolling) return
      
      try {
        const progress = await getUploadProgress()
        setUploadProgress(progress)
        setUploadStatus(progress.message || 'Processing...')
        
        // Continue polling if not complete or error
        if (progress.status !== 'complete' && progress.status !== 'error' && progress.status !== 'not_started') {
          const timeout = setTimeout(pollProgress, 500) // Poll every 500ms
          setProgressPolling(timeout)
        } else {
          // Stop polling when complete
          shouldContinuePolling = false
          setProgressPolling(null)
          if (progress.status === 'complete') {
            // Re-fetch user regard score
            try {
              const data = await fetchUserRegard()
              setUserRegard(data)
              setUploadStatus('Trade history uploaded and analyzed successfully!')
            } catch (err) {
              setUploadStatus('File uploaded, but could not refresh score. Please refresh the page.')
            }
          } else if (progress.status === 'error') {
            setUploadStatus(`Error: ${progress.error || 'Analysis failed'}`)
          }
          setUploading(false)
        }
      } catch (err) {
        console.error('Error polling progress:', err)
        // Continue polling even if there's an error (might be temporary)
        if (shouldContinuePolling) {
          const timeout = setTimeout(pollProgress, 1000) // Poll every 1s on error
          setProgressPolling(timeout)
        }
      }
    }

    try {
      // Start the upload (non-blocking)
      uploadTradeHistory(selectedFile).catch((err) => {
        console.error('Upload error:', err)
        shouldContinuePolling = false
        if (progressPolling) {
          clearTimeout(progressPolling)
          setProgressPolling(null)
        }
        setUploading(false)
        if (err.message?.includes('404') || err.message?.includes('not found')) {
          setUploadStatus('Analysis endpoint not ready yet – your file won\'t be processed.')
        } else {
          setUploadStatus(`Error: ${err.message || 'Could not upload or analyze your trade history. Please check the file format and try again.'}`)
        }
      })
      
      // Start polling after a short delay to let upload start
      setTimeout(() => {
        if (shouldContinuePolling) {
          pollProgress()
        }
      }, 500)
      
      // Clean up file input after a delay
      setTimeout(() => {
        setSelectedFile(null)
        const fileInput = document.getElementById('trade-history-file') as HTMLInputElement
        if (fileInput) fileInput.value = ''
      }, 2000)
    } catch (err: any) {
      console.error('Upload error:', err)
      shouldContinuePolling = false
      if (progressPolling) {
        clearTimeout(progressPolling)
        setProgressPolling(null)
      }
      setUploading(false)
      if (err.message?.includes('404') || err.message?.includes('not found')) {
        setUploadStatus('Analysis endpoint not ready yet – your file won\'t be processed.')
      } else {
        setUploadStatus(`Error: ${err.message || 'Could not upload or analyze your trade history. Please check the file format and try again.'}`)
      }
    }
  }

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (progressPolling) {
        clearTimeout(progressPolling)
      }
    }
  }, [progressPolling])

  const handleTimeframeChange = (value: '24h' | '7d' | '30d') => {
    setDefaultTimeframe(value)
    if (typeof window !== 'undefined') {
      localStorage.setItem('ragard_default_timeframe', value)
    }
  }

  const handleRiskProfileChange = (value: 'conservative' | 'balanced' | 'degen') => {
    setRiskProfile(value)
    if (typeof window !== 'undefined') {
      localStorage.setItem('ragard_risk_profile', value)
    }
  }

  // Get user initials for avatar
  const getUserInitials = (): string => {
    if (user?.firstName && user?.lastName) {
      return (user.firstName[0] + user.lastName[0]).toUpperCase()
    }
    if (user?.firstName) {
      return user.firstName.substring(0, 2).toUpperCase()
    }
    if (user?.email) {
      const parts = user.email.split('@')[0].split('.')
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase()
      }
      return user.email.substring(0, 2).toUpperCase()
    }
    return '?'
  }

  // Get display name from user data
  const getDisplayName = (): string => {
    if (user?.firstName && user?.lastName) {
      return `${user.firstName} ${user.lastName}`
    }
    if (user?.firstName) {
      return user.firstName
    }
    if (user?.lastName) {
      return user.lastName
    }
    // Fallback to email-based name
    if (user?.email) {
      const emailPart = user.email.split('@')[0]
      if (emailPart.includes('.')) {
        return emailPart
          .split('.')
          .map(part => part.charAt(0).toUpperCase() + part.slice(1))
          .join(' ')
      }
      return emailPart.charAt(0).toUpperCase() + emailPart.slice(1)
    }
    return 'User'
  }

  // Format date
  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Never'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    } catch {
      return dateString
    }
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <h1 className="text-5xl font-bold font-display text-ragard-textPrimary">
          Account
        </h1>
        <Card>
          <div className="flex justify-center py-8">
            <RadarLoader message="Loading account..." />
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <h1 className="text-5xl font-bold font-display text-ragard-textPrimary">
        Account
      </h1>

      {!isLoggedIn ? (
        <>
          {/* Logged out state */}
          <Card>
            <div className="space-y-6">
              <div>
                <p className="text-ragard-textSecondary mb-4">
                  You're not logged in. Log in or sign up to use personalized watchlists and generate your User Regard Score.
                </p>
              </div>

              {/* Mode toggle */}
              <div className="flex gap-2 border-b border-slate-800">
                <button
                  onClick={() => {
                    setMode('login')
                    setError(null)
                    setSuccess(null)
                    setPasswordConfirm('')
                    setFirstName('')
                    setLastName('')
                  }}
                  className={`px-4 py-2 font-medium transition-colors ${
                    mode === 'login'
                      ? 'text-ragard-accent border-b-2 border-ragard-accent'
                      : 'text-ragard-textSecondary hover:text-ragard-textPrimary'
                  }`}
                >
                  Log In
                </button>
                <button
                  onClick={() => {
                    setMode('signup')
                    setError(null)
                    setSuccess(null)
                  }}
                  className={`px-4 py-2 font-medium transition-colors ${
                    mode === 'signup'
                      ? 'text-ragard-accent border-b-2 border-ragard-accent'
                      : 'text-ragard-textSecondary hover:text-ragard-textPrimary'
                  }`}
                >
                  Sign Up
                </button>
              </div>

              {/* Auth form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                {mode === 'signup' && (
                  <>
                    <div>
                      <label htmlFor="firstName" className="block text-sm font-medium text-ragard-textSecondary mb-2">
                        First Name
                      </label>
                      <input
                        id="firstName"
                        type="text"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        required
                        className="w-full px-4 py-2 bg-ragard-surface border border-slate-700 rounded-md text-ragard-textPrimary placeholder-ragard-textSecondary focus:outline-none focus:ring-2 focus:ring-ragard-accent focus:border-transparent"
                        placeholder="John"
                        disabled={authLoading}
                      />
                    </div>
                    <div>
                      <label htmlFor="lastName" className="block text-sm font-medium text-ragard-textSecondary mb-2">
                        Last Name
                      </label>
                      <input
                        id="lastName"
                        type="text"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        required
                        className="w-full px-4 py-2 bg-ragard-surface border border-slate-700 rounded-md text-ragard-textPrimary placeholder-ragard-textSecondary focus:outline-none focus:ring-2 focus:ring-ragard-accent focus:border-transparent"
                        placeholder="Doe"
                        disabled={authLoading}
                      />
                    </div>
                  </>
                )}

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-ragard-textSecondary mb-2">
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-4 py-2 bg-ragard-surface border border-slate-700 rounded-md text-ragard-textPrimary placeholder-ragard-textSecondary focus:outline-none focus:ring-2 focus:ring-ragard-accent focus:border-transparent"
                    placeholder="your@email.com"
                    disabled={authLoading}
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-ragard-textSecondary mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      minLength={6}
                      className="w-full px-4 py-2 pr-10 bg-ragard-surface border border-slate-700 rounded-md text-ragard-textPrimary placeholder-ragard-textSecondary focus:outline-none focus:ring-2 focus:ring-ragard-accent focus:border-transparent"
                      placeholder="••••••••"
                      disabled={authLoading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-ragard-textSecondary hover:text-ragard-textPrimary transition-colors"
                      tabIndex={-1}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? (
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                          />
                        </svg>
                      ) : (
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                          />
                        </svg>
                      )}
                    </button>
                  </div>
                </div>

                {mode === 'signup' && (
                  <div>
                    <label htmlFor="passwordConfirm" className="block text-sm font-medium text-ragard-textSecondary mb-2">
                      Confirm Password
                    </label>
                    <div className="relative">
                      <input
                        id="passwordConfirm"
                        type={showPasswordConfirm ? 'text' : 'password'}
                        value={passwordConfirm}
                        onChange={(e) => setPasswordConfirm(e.target.value)}
                        required
                        minLength={6}
                        className="w-full px-4 py-2 pr-10 bg-ragard-surface border border-slate-700 rounded-md text-ragard-textPrimary placeholder-ragard-textSecondary focus:outline-none focus:ring-2 focus:ring-ragard-accent focus:border-transparent"
                        placeholder="••••••••"
                        disabled={authLoading}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-ragard-textSecondary hover:text-ragard-textPrimary transition-colors"
                        tabIndex={-1}
                        aria-label={showPasswordConfirm ? 'Hide password' : 'Show password'}
                      >
                        {showPasswordConfirm ? (
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                            />
                          </svg>
                        ) : (
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                            />
                          </svg>
                        )}
                      </button>
                    </div>
                    {passwordConfirm && password !== passwordConfirm && (
                      <p className="mt-1 text-sm text-ragard-danger">Passwords do not match</p>
                    )}
                  </div>
                )}

                {error && (
                  <div className="p-3 bg-ragard-danger/20 border border-ragard-danger/30 rounded-md text-ragard-danger text-sm">
                    {error}
                  </div>
                )}

                {success && (
                  <div className="p-3 bg-ragard-success/20 border border-ragard-success/30 rounded-md text-ragard-success text-sm">
                    {success}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={
                    authLoading ||
                    !email ||
                    !password ||
                    (mode === 'signup' && (!firstName || !lastName || !passwordConfirm || password !== passwordConfirm))
                  }
                  className="w-full px-4 py-2 bg-ragard-accent text-white rounded-md hover:bg-ragard-accent/80 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {authLoading ? 'Processing...' : mode === 'login' ? 'Log In' : 'Sign Up'}
                </button>
              </form>
            </div>
          </Card>
        </>
      ) : (
        <>
          {/* Logged in state - Full Account Page */}
          
          {/* Section A: Profile Header */}
          <Card>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-ragard-accent/20 border-2 border-ragard-accent/30 flex items-center justify-center">
                  <span className="text-2xl font-bold text-ragard-accent">
                    {getUserInitials()}
                  </span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold font-display text-ragard-textPrimary">
                    {getDisplayName()}
                  </h2>
                  <p className="text-sm text-ragard-textSecondary mt-1">
                    {user?.email || ''}
                  </p>
                  <p className="text-xs text-ragard-textSecondary mt-0.5">
                    Member since {user?.createdAt ? formatDate(user.createdAt) : '(login again to see date)'}
                  </p>
                </div>
              </div>
              <button
                onClick={handleSignOut}
                disabled={authLoading}
                className="px-4 py-2 bg-ragard-danger/20 text-ragard-danger border border-ragard-danger/30 rounded-md hover:bg-ragard-danger/30 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {authLoading ? 'Logging out...' : 'Log Out'}
              </button>
            </div>
          </Card>

          {/* Section B: User Regard Score & Trade History */}
          <Card>
            <h2 className="text-2xl font-bold font-display text-ragard-textPrimary mb-6">
              Your Regard Score
            </h2>
            
            {regardLoading ? (
              <div className="flex justify-center py-8">
                <RadarLoader message="Loading your Regard Score..." />
              </div>
            ) : !userRegard || userRegard.regardScore === null || userRegard.sampleSize === 0 ? (
              <div className="space-y-6">
                <div className="text-center py-8 space-y-3">
                  <h3 className="text-xl font-bold text-ragard-textPrimary">
                    No Regard Score yet
                  </h3>
                  <p className="text-ragard-textSecondary">
                    Upload your trade history to calculate how well you trade the things Ragard flags.
                  </p>
                </div>
                
                {/* Trade History Upload Section */}
                <div className="border-t border-slate-800 pt-6">
                  <h3 className="text-lg font-semibold font-display text-ragard-textPrimary mb-4">
                    Upload Trade History
                  </h3>
                  <div className="space-y-4">
                    <p className="text-ragard-textSecondary text-sm">
                      Upload your trading history (CSV or supported format) so Ragard can analyze your performance and update your Regard Score.
                    </p>
                    
                    <div className="space-y-3">
                      <div>
                        <label htmlFor="trade-history-file" className="block text-sm font-medium text-ragard-textSecondary mb-2">
                          Select Trade History File
                        </label>
                        <input
                          id="trade-history-file"
                          type="file"
                          accept=".csv"
                          onChange={handleFileSelect}
                          disabled={uploading}
                          className="w-full px-4 py-2 bg-ragard-surface border border-slate-700 rounded-md text-ragard-textPrimary text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-ragard-accent file:text-white hover:file:bg-ragard-accent/80 disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                      </div>
                      
                      <button
                        onClick={handleUpload}
                        disabled={!selectedFile || uploading}
                        className="w-full px-4 py-2 bg-ragard-accent text-white rounded-md hover:bg-ragard-accent/80 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {uploading ? 'Uploading & Analyzing...' : 'Upload & Analyze'}
                      </button>
                      
                      {/* Progress Bar */}
                      {uploading && uploadProgress && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-ragard-textSecondary">{uploadProgress.message || 'Processing...'}</span>
                            <span className="text-ragard-textPrimary font-semibold">{uploadProgress.percentage.toFixed(0)}%</span>
                          </div>
                          <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                            <div
                              className="h-full bg-ragard-accent transition-all duration-300 ease-out"
                              style={{ width: `${uploadProgress.percentage}%` }}
                            />
                          </div>
                          <div className="text-xs text-ragard-textSecondary">
                            Step {uploadProgress.current_step} of {uploadProgress.total_steps}: {uploadProgress.status}
                          </div>
                        </div>
                      )}
                      
                      {uploadStatus && (
                        <div className={`p-3 rounded-md text-sm ${
                          uploadStatus.includes('Error') || uploadStatus.includes('not ready')
                            ? 'bg-ragard-danger/20 border border-ragard-danger/30 text-ragard-danger'
                            : uploadStatus.includes('success')
                            ? 'bg-ragard-success/20 border border-ragard-success/30 text-ragard-success'
                            : 'bg-ragard-surfaceAlt/50 border border-slate-800 text-ragard-textSecondary'
                        }`}>
                          {uploadStatus}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-8">
                {/* Score Display */}
                <div>
                  <div className="flex items-start gap-12 mb-6">
                    {/* Score Gauge on the left */}
                    <div className="w-48 h-48 flex-shrink-0">
                      <RagardScoreGauge score={userRegard.regardScore} size="lg" />
                    </div>
                    
                    {/* Stats on the right */}
                    <div className="flex-1 space-y-3 pt-2">
                      <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                        <div>
                          <span className="text-ragard-textSecondary">Wins: </span>
                          <span className="font-semibold text-ragard-textPrimary">{userRegard.wins}</span>
                        </div>
                        <div>
                          <span className="text-ragard-textSecondary">Losses: </span>
                          <span className="font-semibold text-ragard-textPrimary">{userRegard.losses}</span>
                        </div>
                        <div>
                          <span className="text-ragard-textSecondary">Win rate: </span>
                          <span className="font-semibold text-ragard-textPrimary">
                            {userRegard.winRate !== null ? `${(userRegard.winRate * 100).toFixed(1)}%` : 'N/A'}
                          </span>
                        </div>
                        <div>
                          <span className="text-ragard-textSecondary">Trades analyzed: </span>
                          <span className="font-semibold text-ragard-textPrimary">{userRegard.sampleSize}</span>
                        </div>
                      </div>
                      <div className="text-xs text-ragard-textSecondary pt-1">
                        Last updated: {formatDate(userRegard.lastUpdated)}
                      </div>
                    </div>
                  </div>
                  
                  <p className="text-sm text-ragard-textSecondary">
                    Your Regard Score uses your uploaded trade history plus AI analysis to measure how often you're on the right side of your own plays.
                  </p>
                  
                  {userRegard.sampleSize < 20 && (
                    <div className="mt-4 p-3 bg-yellow-500/20 border border-yellow-500/30 rounded-md text-yellow-500 text-sm">
                      Low sample size – your score will get more accurate as you upload more history.
                    </div>
                  )}
                  
                  {/* Download Report Button */}
                  <div className="mt-6 pt-6 border-t border-slate-800">
                    <button
                      onClick={async () => {
                        if (!userRegard || userRegard.sampleSize === 0) return
                        
                        setDownloadingReport(true)
                        try {
                          const blob = await downloadUserReport()
                          const url = window.URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          const dateStr = new Date().toISOString().split('T')[0]
                          const displayName = getDisplayName().replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '').substring(0, 20)
                          a.download = `ragard-trading-report-${displayName}-${dateStr}.pdf`
                          document.body.appendChild(a)
                          a.click()
                          window.URL.revokeObjectURL(url)
                          document.body.removeChild(a)
                        } catch (err: any) {
                          console.error('Error downloading report:', err)
                          alert(err.message || 'Could not generate your report. Try again in a bit.')
                        } finally {
                          setDownloadingReport(false)
                        }
                      }}
                      disabled={downloadingReport || !userRegard || userRegard.sampleSize === 0}
                      className="w-full px-4 py-3 bg-ragard-accent/20 text-ragard-accent border border-ragard-accent/30 rounded-md hover:bg-ragard-accent/30 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {downloadingReport ? (
                        <>
                          <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          <span>Generating report...</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <span>Download Full Report</span>
                        </>
                      )}
                    </button>
                    <p className="mt-2 text-xs text-ragard-textSecondary text-center">
                      Get a PDF breakdown of your trades, Regard score, and degenerate tendencies.
                    </p>
                  </div>
                </div>
                
                {/* Trade History Upload Section */}
                <div className="border-t border-slate-800 pt-6">
                  <h3 className="text-lg font-semibold font-display text-ragard-textPrimary mb-4">
                    Update Trade History
                  </h3>
                  <div className="space-y-4">
                    <p className="text-ragard-textSecondary text-sm">
                      Upload a new trade history file to update your Regard Score with your latest trades.
                    </p>
                    
                    <div className="space-y-3">
                      <div>
                        <label htmlFor="trade-history-file" className="block text-sm font-medium text-ragard-textSecondary mb-2">
                          Select Trade History File
                        </label>
                        <input
                          id="trade-history-file"
                          type="file"
                          accept=".csv"
                          onChange={handleFileSelect}
                          disabled={uploading}
                          className="w-full px-4 py-2 bg-ragard-surface border border-slate-700 rounded-md text-ragard-textPrimary text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-ragard-accent file:text-white hover:file:bg-ragard-accent/80 disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                      </div>
                      
                      <button
                        onClick={handleUpload}
                        disabled={!selectedFile || uploading}
                        className="w-full px-4 py-2 bg-ragard-accent text-white rounded-md hover:bg-ragard-accent/80 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {uploading ? 'Uploading & Analyzing...' : 'Upload & Analyze'}
                      </button>
                      
                      {/* Progress Bar */}
                      {uploading && uploadProgress && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-ragard-textSecondary">{uploadProgress.message || 'Processing...'}</span>
                            <span className="text-ragard-textPrimary font-semibold">{uploadProgress.percentage.toFixed(0)}%</span>
                          </div>
                          <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                            <div
                              className="h-full bg-ragard-accent transition-all duration-300 ease-out"
                              style={{ width: `${uploadProgress.percentage}%` }}
                            />
                          </div>
                          <div className="text-xs text-ragard-textSecondary">
                            Step {uploadProgress.current_step} of {uploadProgress.total_steps}: {uploadProgress.status}
                          </div>
                        </div>
                      )}
                      
                      {uploadStatus && (
                        <div className={`p-3 rounded-md text-sm ${
                          uploadStatus.includes('Error') || uploadStatus.includes('not ready')
                            ? 'bg-ragard-danger/20 border border-ragard-danger/30 text-ragard-danger'
                            : uploadStatus.includes('success')
                            ? 'bg-ragard-success/20 border border-ragard-success/30 text-ragard-success'
                            : 'bg-ragard-surfaceAlt/50 border border-slate-800 text-ragard-textSecondary'
                        }`}>
                          {uploadStatus}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </Card>

          {/* Section D: Ragard Activity */}
          <Card>
            <h2 className="text-2xl font-bold font-display text-ragard-textPrimary mb-4">
              Your Ragard Activity
            </h2>
            
            {activityLoading ? (
              <div className="flex justify-center py-4">
                <RadarLoader message="Loading activity..." />
              </div>
            ) : (
              <div className="space-y-6">
                {/* Watchlists Summary */}
                <div className="border-b border-slate-800 pb-4">
                  <h3 className="text-lg font-semibold text-ragard-textPrimary mb-3">
                    Watchlists
                  </h3>
                  {watchlists.length === 0 ? (
                    <p className="text-ragard-textSecondary text-sm mb-3">
                      No watchlists yet. Add tickers from the homepage once you start using Ragard.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-ragard-textSecondary text-sm">
                            Watchlists: <span className="font-semibold text-ragard-textPrimary">{watchlists.length}</span>
                          </p>
                          <p className="text-ragard-textSecondary text-sm">
                            Tickers watched: <span className="font-semibold text-ragard-textPrimary">{totalTickers}</span>
                          </p>
                        </div>
                        <button
                          onClick={() => router.push('/')}
                          className="px-4 py-2 bg-ragard-accent text-white rounded-md hover:bg-ragard-accent/80 transition-colors font-medium text-sm"
                        >
                          Open Watchlist
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Saved Analyses Summary */}
                <div>
                  <h3 className="text-lg font-semibold text-ragard-textPrimary mb-3">
                    Saved Analyses
                  </h3>
                  {savedAnalyses.length === 0 ? (
                    <p className="text-ragard-textSecondary text-sm mb-3">
                      No saved analyses yet.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-ragard-textSecondary text-sm mb-2">
                        Saved analyses: <span className="font-semibold text-ragard-textPrimary">{savedAnalyses.length}</span>
                      </p>
                      <div className="space-y-2">
                        {savedAnalyses.slice(0, 3).map((analysis) => {
                          // Extract metadata from snapshot
                          const snapshot = analysis.snapshot || {}
                          const pageTitle = snapshot.title || analysis.title || 'Untitled'
                          const pageUrl = snapshot.url || analysis.url || null
                          const hostname = snapshot.hostname || analysis.hostname || (pageUrl ? new URL(pageUrl).hostname : null)
                          const score = snapshot.score || analysis.score || null
                          
                          return (
                            <div key={analysis.id} className="text-sm border-b border-slate-800 pb-2 last:border-b-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-semibold text-ragard-textPrimary">{analysis.ticker}</span>
                                {score !== null && (
                                  <span className="text-xs px-2 py-0.5 rounded-full bg-ragard-surfaceAlt text-ragard-textSecondary">
                                    Score: {score}
                                  </span>
                                )}
                                <span className="text-ragard-textSecondary text-xs ml-auto">
                                  {formatDate(analysis.created_at)}
                                </span>
                              </div>
                              {pageTitle && (
                                <div className="text-ragard-textSecondary text-xs mb-1 truncate" title={pageTitle}>
                                  {pageTitle}
                                </div>
                              )}
                              {pageUrl && (
                                <a
                                  href={pageUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-ragard-accent hover:text-ragard-accent/80 text-xs truncate block"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {hostname || pageUrl}
                                </a>
                              )}
                            </div>
                          )
                        })}
                      </div>
                      <button
                        onClick={() => router.push('/account/saved-analyses')}
                        className="mt-2 px-4 py-2 bg-ragard-accent text-white rounded-md hover:bg-ragard-accent/80 transition-colors font-medium text-sm"
                      >
                        View All Saved Analyses
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </Card>

          {/* Section E: Settings & Preferences */}
          <Card>
            <h2 className="text-2xl font-bold font-display text-ragard-textPrimary mb-4">
              Settings & Preferences
            </h2>
            
            <div className="space-y-6">
              <div>
                <label htmlFor="default-timeframe" className="block text-sm font-medium text-ragard-textSecondary mb-2">
                  Default Timeframe
                </label>
                <select
                  id="default-timeframe"
                  value={defaultTimeframe}
                  onChange={(e) => handleTimeframeChange(e.target.value as '24h' | '7d' | '30d')}
                  className="w-full px-4 py-2 bg-ragard-surface border border-slate-700 rounded-md text-ragard-textPrimary focus:outline-none focus:ring-2 focus:ring-ragard-accent focus:border-transparent"
                >
                  <option value="24h">24 hours</option>
                  <option value="7d">7 days</option>
                  <option value="30d">30 days</option>
                </select>
              </div>

              <div>
                <label htmlFor="risk-profile" className="block text-sm font-medium text-ragard-textSecondary mb-2">
                  Risk Profile
                </label>
                <select
                  id="risk-profile"
                  value={riskProfile}
                  onChange={(e) => handleRiskProfileChange(e.target.value as 'conservative' | 'balanced' | 'degen')}
                  className="w-full px-4 py-2 bg-ragard-surface border border-slate-700 rounded-md text-ragard-textPrimary focus:outline-none focus:ring-2 focus:ring-ragard-accent focus:border-transparent"
                >
                  <option value="conservative">Conservative</option>
                  <option value="balanced">Balanced</option>
                  <option value="degen">Degen</option>
                </select>
              </div>

              <div className="p-4 bg-ragard-surfaceAlt/50 border border-slate-800 rounded-md">
                <p className="text-xs text-ragard-textSecondary">
                  Settings are saved locally. Future updates will sync preferences to your account.
                </p>
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
