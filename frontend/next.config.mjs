/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactCompiler: true,
  allowedDevOrigins: process.env.ALLOWED_DEV_ORIGINS
    ? process.env.ALLOWED_DEV_ORIGINS.split(",")
    : ["localhost"],
  images: {
    dangerouslyAllowLocalIP: process.env.NODE_ENV === "development",
    remotePatterns: [
      {
        protocol: "https",
        hostname: process.env.NEXTJS_IMAGE_HOST || "localhost",
      },
      {
        protocol: "https",
        hostname: process.env.NEXTJS_PROD_IMAGE_HOST,
      },
    ],
    localPatterns: [
      {
        pathname: "/real-estate/**",
      },
      {
        pathname: "/assets/**",
      },
    ],
  },
  experimental: {
    serverActions: {
      bodySizeLimit: 5 * 1024 * 1024, // Increase limit to 5 MB
      allowedOrigins: process.env.SERVER_ACTIONS_ALLOWED_ORIGINS
        ? process.env.SERVER_ACTIONS_ALLOWED_ORIGINS.split(",")
        : [],
    },
  },
};

export default nextConfig;
