/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        dark: {
          50: "#e6edf6",
          100: "#c0d0e2",
          200: "#8aa5c5",
          300: "#5a7da8",
          400: "#385d8a",
          500: "#1f4470",
          600: "#143258",
          700: "#0e2743",
          800: "#091c30",
          900: "#04101e",
          950: "#020815",
        },
        accent: {
          cyan: "#22d3ee",
          purple: "#a78bfa",
          green: "#22c55e",
          red: "#ef4444",
          yellow: "#eab308",
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}