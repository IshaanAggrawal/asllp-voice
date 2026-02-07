/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    env: {
        NEXT_PUBLIC_DJANGO_API_URL: process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000',
        NEXT_PUBLIC_FASTAPI_WS_URL: process.env.NEXT_PUBLIC_FASTAPI_WS_URL || 'ws://localhost:8001',
    },
}

module.exports = nextConfig
