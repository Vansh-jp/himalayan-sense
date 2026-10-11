/** @type {import('tailwindcss').Config} */
// tailwind.config.js
module.exports = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0fdf4',
          600: '#16a34a',
          800: '#166534',
        },
        risk: {
          green: '#22c55e',   // Low risk
          yellow: '#eab308',  // Moderate risk
          orange: '#f97316',  // High risk
          red: '#ef4444',     // Severe risk
        }
      }
    }
  },
  plugins: [require('@tailwindcss/forms')],
}