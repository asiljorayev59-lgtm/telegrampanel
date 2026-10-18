export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        panel: 'var(--panel)',
        hover: 'var(--hover)',
        line: 'var(--line)',
        txt: 'var(--txt)',
        sub: 'var(--sub)',
        accent: 'var(--accent)',
        out: 'var(--out)',
        inc: 'var(--inc)',
      },
    },
  },
  plugins: [],
};
