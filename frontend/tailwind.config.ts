import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'sans-serif'],
        display: ['var(--font-space-grotesk)', 'Space Grotesk', 'sans-serif'],
      },
      colors: {
        ragard: {
          background: '#050810',
          surface: '#0B101A',
          surfaceAlt: '#111827',
          accent: '#22D3EE',
          secondary: '#4ADE80',
          textPrimary: '#F9FAFB',
          textSecondary: '#9CA3AF',
          textMuted: '#4B5563',
          danger: '#EF4444',
          warning: '#FACC15',
          success: '#22C55E',
          score: {
            bad: '#EF4444',
            ultra: '#F97316',
            spicy: '#EAB308',
            respect: '#22C55E',
            elite: '#22D3EE',
          },
        },
      },
      boxShadow: {
        'ragard-glow': '0 0 20px rgba(34, 211, 238, 0.1)',
        'ragard-glow-sm': '0 0 10px rgba(34, 211, 238, 0.05)',
      },
    },
  },
  plugins: [],
}
export default config

