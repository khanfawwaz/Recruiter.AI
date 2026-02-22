import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000,
        proxy: {
            '/analyze': 'http://localhost:5000',
            '/override': 'http://localhost:5000',
            '/finalize': 'http://localhost:5000',
            '/session': 'http://localhost:5000',
            '/health': 'http://localhost:5000',
        }
    }
})
