/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./pages/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fdf8f3",
          100: "#f5ebe0",
          200: "#e8d0b3",
          300: "#d4a96a",
          400: "#c4893d",
          500: "#a06930",
          600: "#7d5025",
        },
        surface: "#fdfaf7",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
