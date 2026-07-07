/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      borderRadius: {
        btn: '12px',
        card: '22px',
        input: '10px',
      },
      fontFamily: {
        sans: ['Barlow', 'sans-serif'],
        condensed: ['Barlow Semi Condensed', 'sans-serif'],
      },
      colors: {
        bg: 'var(--bg)',
        surface: 'var(--bg-surface)',
        elevated: 'var(--bg-elevated)',
        card: 'var(--card-bg)',
        border: 'var(--border)',
        'border-accent': 'var(--border-accent)',
        text: 'var(--text)',
        muted: 'var(--text-muted)',
        accent: 'var(--neon-green)',
        info: 'var(--neon-blue)',
        danger: 'var(--danger)',
      },
    },
  },
  plugins: [],
};
