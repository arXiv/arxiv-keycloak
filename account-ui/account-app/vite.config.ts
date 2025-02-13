import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import svgr from "vite-plugin-svgr"; // Import SVGR plugin

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), svgr()],
  base: "/user/",
  server: {
    port: 21514,
    host: '0.0.0.0',
    allowedHosts: ['0.0.0.0', '127.0.0.1', 'localhost', 'localhost.arxiv.org'],
  },
})
