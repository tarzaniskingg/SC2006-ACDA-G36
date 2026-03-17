import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // For GitHub Pages: set to '/<repo-name>/' e.g. '/SC2006-ACDA-G36/'
  // For custom domain or root deploy: set to '/'
  base: process.env.GITHUB_PAGES ? '/SC2006-ACDA-G36/' : '/',
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
