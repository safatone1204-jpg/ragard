/**
 * Environment variable validation for frontend.
 * Validates required env vars at build/runtime and shows clear errors.
 */

const REQUIRED_ENV_VARS = [
  'NEXT_PUBLIC_API_BASE_URL',
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
] as const

interface ValidationResult {
  valid: boolean
  missing: string[]
  errors: string[]
}

/**
 * Validate environment variables.
 * Call this at build time or early in the app lifecycle.
 */
export function validateEnvVars(): ValidationResult {
  const missing: string[] = []
  const errors: string[] = []

  for (const varName of REQUIRED_ENV_VARS) {
    const value = process.env[varName]
    if (!value || value.trim() === '') {
      missing.push(varName)
    }
  }

  // Validate API_BASE_URL format if set
  const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL
  if (apiUrl && apiUrl.trim() !== '') {
    try {
      new URL(apiUrl)
    } catch {
      errors.push(`NEXT_PUBLIC_API_BASE_URL is not a valid URL: ${apiUrl}`)
    }
  }

  // Validate Supabase URL format if set
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  if (supabaseUrl && supabaseUrl.trim() !== '') {
    try {
      new URL(supabaseUrl)
    } catch {
      errors.push(`NEXT_PUBLIC_SUPABASE_URL is not a valid URL: ${supabaseUrl}`)
    }
  }

  return {
    valid: missing.length === 0 && errors.length === 0,
    missing,
    errors,
  }
}

/**
 * Show error UI if env vars are missing.
 * Call this in a React component or error boundary.
 */
export function showEnvErrorUI(result: ValidationResult): React.ReactElement | null {
  if (result.valid) {
    return null
  }

  return (
    <div style={{
      padding: '2rem',
      maxWidth: '600px',
      margin: '2rem auto',
      background: '#1e1e1e',
      color: '#fff',
      borderRadius: '8px',
      border: '2px solid #ef4444',
    }}>
      <h2 style={{ color: '#ef4444', marginTop: 0 }}>Configuration Error</h2>
      <p>Missing or invalid environment variables:</p>
      {result.missing.length > 0 && (
        <ul>
          {result.missing.map((varName) => (
            <li key={varName}>
              <code style={{ background: '#2a2a2a', padding: '2px 6px', borderRadius: '4px' }}>
                {varName}
              </code>
            </li>
          ))}
        </ul>
      )}
      {result.errors.length > 0 && (
        <ul>
          {result.errors.map((error, idx) => (
            <li key={idx} style={{ color: '#fbbf24' }}>{error}</li>
          ))}
        </ul>
      )}
      <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#9ca3af' }}>
        Please set these variables in your <code>.env.local</code> file.
        See <code>frontend/env.example</code> for an example configuration.
      </p>
    </div>
  )
}

// Validate at module load time (for build-time checks)
if (typeof window === 'undefined') {
  // Server-side (build time)
  const result = validateEnvVars()
  if (!result.valid) {
    console.error('❌ Environment variable validation failed:')
    result.missing.forEach((varName) => {
      console.error(`  Missing: ${varName}`)
    })
    result.errors.forEach((error) => {
      console.error(`  Error: ${error}`)
    })
    console.error('\nPlease set these variables in your .env.local file.')
    console.error('See frontend/env.example for an example configuration.')
    // Don't exit in Next.js build - let it fail naturally if needed
  }
}

