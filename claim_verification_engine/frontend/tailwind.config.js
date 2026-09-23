/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        paper: '#F7F5F0',
        ink: '#221F1B',
        'ink-soft': '#6B655C',
        line: '#E3DED3',
        verified: {
          DEFAULT: '#3F6B52',
          soft: '#EAF0EA',
        },
        refuted: {
          DEFAULT: '#9C4A3C',
          soft: '#F5E9E5',
        },
        mixed: {
          DEFAULT: '#A57726',
          soft: '#F5EDDE',
        },
        unverifiable: {
          DEFAULT: '#7A7669',
          soft: '#EDEBE5',
        },
      },
      fontFamily: {
        serif: ['"Newsreader"', 'Georgia', 'serif'],
        sans: ['"Inter"', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
