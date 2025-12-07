/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './app/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // LinkedIn Professional Color Palette
        linkedin: {
          50: '#E7F3FF',
          100: '#D0E7FF',
          200: '#A1CFFF',
          300: '#70B5F9',
          400: '#0077B5',
          500: '#0A66C2', // Primary LinkedIn Blue
          600: '#004182', // Dark Blue
          700: '#002D5C',
          800: '#001A36',
          900: '#000D1B',
        },
        professional: {
          bg: '#F3F2EF', // LinkedIn background
          'bg-light': '#FFFFFF',
          'bg-hover': '#F5F5F3',
          border: '#E0E0E0',
          'border-light': '#EDEBE9',
          text: '#000000',
          'text-secondary': '#666666',
          'text-tertiary': '#8E8E8E',
          success: '#057642',
          'success-light': '#E8F5E9',
          warning: '#B54708',
          'warning-light': '#FEF3C7',
          error: '#C8102E',
          'error-light': '#FEE2E2',
        },
        primary: {
          50: '#E7F3FF',
          100: '#D0E7FF',
          200: '#A1CFFF',
          300: '#70B5F9',
          400: '#0077B5',
          500: '#0A66C2', // LinkedIn Primary
          600: '#004182',
          700: '#002D5C',
          800: '#001A36',
          900: '#000D1B',
        },
        trust: {
          blue: '#0A66C2',
          dark: '#004182',
          light: '#70B5F9',
        },
        premium: {
          blue: {
            50: '#E7F3FF',
            100: '#D0E7FF',
            200: '#A1CFFF',
            300: '#70B5F9',
            400: '#0077B5',
            500: '#0A66C2',
            600: '#004182',
            700: '#002D5C',
            800: '#001A36',
            900: '#000D1B',
          },
          slate: {
            50: '#F3F2EF',
            100: '#FFFFFF',
            200: '#F5F5F3',
            300: '#E0E0E0',
            400: '#EDEBE9',
            500: '#8E8E8E',
            600: '#666666',
            700: '#000000',
            800: '#001A36',
            900: '#000D1B',
          }
        }
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        display: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-down': 'slideDown 0.5s ease-out',
        'slide-in-left': 'slideInLeft 0.6s ease-out',
        'slide-in-right': 'slideInRight 0.6s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'float-slow': 'float 8s ease-in-out infinite',
        'float-fast': 'float 4s ease-in-out infinite',
        'glow': 'glow 3s ease-in-out infinite',
        'glow-linkedin': 'glowLinkedIn 2s ease-in-out infinite',
        'shimmer': 'shimmer 2s infinite',
        'bounce-slow': 'bounce 3s infinite',
        'bounce-gentle': 'bounceGentle 2s ease-in-out infinite',
        'scale-in': 'scaleIn 0.3s ease-out',
        'scale-out': 'scaleOut 0.3s ease-out',
        'fade-up': 'fadeUp 0.6s ease-out',
        'fade-down': 'fadeDown 0.6s ease-out',
        'slide-fade': 'slideFade 0.5s ease-out',
        'wave': 'wave 2s ease-in-out infinite',
        'ripple': 'ripple 1.5s ease-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInLeft: {
          '0%': { transform: 'translateX(-30px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(30px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
          '50%': { transform: 'translateY(-20px) rotate(2deg)' },
        },
        bounceGentle: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(10, 102, 194, 0.3), 0 0 40px rgba(10, 102, 194, 0.2)' },
          '50%': { boxShadow: '0 0 30px rgba(10, 102, 194, 0.5), 0 0 60px rgba(10, 102, 194, 0.3)' },
        },
        glowLinkedIn: {
          '0%, 100%': { boxShadow: '0 0 15px rgba(10, 102, 194, 0.4)' },
          '50%': { boxShadow: '0 0 25px rgba(10, 102, 194, 0.6), 0 0 35px rgba(10, 102, 194, 0.4)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        scaleOut: {
          '0%': { transform: 'scale(1)', opacity: '1' },
          '100%': { transform: 'scale(0.95)', opacity: '0' },
        },
        fadeUp: {
          '0%': { transform: 'translateY(30px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeDown: {
          '0%': { transform: 'translateY(-30px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideFade: {
          '0%': { transform: 'translateX(-20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        wave: {
          '0%, 100%': { transform: 'rotate(0deg)' },
          '25%': { transform: 'rotate(5deg)' },
          '75%': { transform: 'rotate(-5deg)' },
        },
        ripple: {
          '0%': { transform: 'scale(0.8)', opacity: '1' },
          '100%': { transform: 'scale(2.4)', opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}

