/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',  // Tối ưu cho Vercel deployment
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

export default nextConfig;
