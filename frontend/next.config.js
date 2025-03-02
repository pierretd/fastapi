/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['cdn.akamai.steamstatic.com', 'steamcdn-a.akamaihd.net', 'cdn.cloudflare.steamstatic.com'],
  },
  async rewrites() {
    const isProduction = process.env.NODE_ENV === 'production';
    const apiUrl = 'https://fastapi-5aw3.onrender.com';
    
    return [
      {
        source: '/api/py/:path*',
        destination: `${apiUrl}/:path*`,
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
};

module.exports = nextConfig;
