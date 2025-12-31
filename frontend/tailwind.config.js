/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Python-inspired color palette
        python: {
          blue: '#306998',      // Python blue
          yellow: '#FFD43B',    // Python yellow
          darkBlue: '#1e415e',  // Darker Python blue
        },
        // Dark theme colors
        dark: {
          900: '#0d0d0d',       // Near black background
          800: '#1a1a2e',       // Dark purple-tinted background
          700: '#16213e',       // Dark blue-tinted background
          600: '#1f2937',       // Card background
          500: '#374151',       // Border color
        },
        // Accent colors - rich purples and blues
        accent: {
          purple: '#7c3aed',    // Vibrant purple
          purpleLight: '#a78bfa', // Light purple
          purpleDark: '#5b21b6',  // Dark purple
          blue: '#3b82f6',      // Vibrant blue
          blueLight: '#60a5fa', // Light blue
          blueDark: '#1d4ed8',  // Dark blue
          cyan: '#06b6d4',      // Cyan accent
        },
      },
    },
  },
  plugins: [],
}
