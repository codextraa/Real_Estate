/** @type {import('next').NextConfig} */
const nextConfig = {
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
        hostname: "codextra-s3-media.s3.amazonaws.com",
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
    },
  },
};

export default nextConfig;
