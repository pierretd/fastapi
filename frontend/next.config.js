/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['cdn.akamai.steamstatic.com', 'steamcdn-a.akamaihd.net', 'cdn.cloudflare.steamstatic.com'],
  },
  async rewrites() {
    const isProduction = process.env.NODE_ENV === 'production';
    const apiUrl = isProduction 
      ? 'https://fastapi-5aw3.onrender.com' 
      : 'http://localhost:8008';
    
    return [
      {
        source: '/api/py/:path*',
        destination: `${apiUrl}/api/py/:path*`,
      },
      {
        source: '/docs',
        destination: `${apiUrl}/docs`,
      },
      {
        source: '/openapi.json',
        destination: `${apiUrl}/openapi.json`,
      },
    ];
  },
  // Add experimental features
  experimental: {
    // This gives us access to client component features in server components
    serverActions: true,
  },
};

module.exports = nextConfig;
