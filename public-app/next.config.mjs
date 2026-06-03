/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Shared design tokens live in the workspace package.
  transpilePackages: ["@ama/tokens"],
};

export default nextConfig;
