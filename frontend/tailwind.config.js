/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        dark: {
          950: '#020408',
          900: '#060d1a',
          800: '#0a1628',
          700: '#0f2040',
          600: '#162d58',
        },
        brand: {
          50:  '#eef5ff',
          100: '#d9e9ff',
          200: '#bcd6ff',
          300: '#8eb9fe',
          400: '#5990fc',
          500: '#3b72f8',
          600: '#2354ed',
          700: '#1b3fd9',
          800: '#1c35b0',
          900: '#1c328b',
        },
        success: {
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
        },
        warning: {
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
        },
        danger: {
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
        },
        violet: {
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'grid-pattern': "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Cpath d='M0 0h40v40H0z' fill='none'/%3E%3Cpath d='M0 0h1v40H0zM40 0h1v40H0zM0 0v1h40V0zM0 40v1h40V0z' fill='%23162d5820'/%3E%3C/svg%3E\")",
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow':       'glow 2s ease-in-out infinite alternate',
        'slide-in':   'slideIn 0.3s ease-out',
        'fade-in':    'fadeIn 0.5s ease-out',
      },
      keyframes: {
        glow: {
          '0%':   { boxShadow: '0 0 5px rgba(59,114,248,0.3)' },
          '100%': { boxShadow: '0 0 20px rgba(59,114,248,0.7)' },
        },
        slideIn: {
          '0%':   { transform: 'translateX(-10px)', opacity: 0 },
          '100%': { transform: 'translateX(0)',      opacity: 1 },
        },
        fadeIn: {
          '0%':   { opacity: 0 },
          '100%': { opacity: 1 },
        },
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.05)',
        'glow-blue':    '0 0 20px rgba(59,114,248,0.4)',
        'glow-green':   '0 0 20px rgba(34,197,94,0.4)',
        'glow-amber':   '0 0 20px rgba(245,158,11,0.4)',
        'glow-red':     '0 0 20px rgba(239,68,68,0.4)',
      },
    },
  },
  plugins: [],
}
