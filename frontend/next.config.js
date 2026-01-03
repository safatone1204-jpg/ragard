/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enable standalone output for Docker
  output: 'standalone',
  // Production optimizations
  compress: true,
  poweredByHeader: false,
  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  // Security headers
  async headers() {
    // Only add CSP in production - in development, it's too restrictive
    const isProduction = process.env.NODE_ENV === 'production'
    
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin'
          },
          // Only add CSP in production to avoid blocking localhost in development
          ...(isProduction ? [{
            key: 'Content-Security-Policy',
            value: (() => {
              // Get API base URL from environment, extract domain
              const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '';
              let connectSrc = "'self' https://*.supabase.co https://*.supabase.in";
              
              // If API URL is set, extract domain and add to connect-src
              if (apiUrl) {
                try {
                  const apiDomain = new URL(apiUrl).origin;
                  connectSrc += ` ${apiDomain}`;
                } catch (e) {
                  // If URL parsing fails, just use the original
                  console.warn('Failed to parse NEXT_PUBLIC_API_BASE_URL for CSP');
                }
              }
              
              return [
                "default-src 'self'",
                "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self' data:",
                `connect-src ${connectSrc}`,
                "frame-ancestors 'self'",
              ].join('; ');
            })()
          }] : []),
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig

