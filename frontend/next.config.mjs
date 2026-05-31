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
        hostname: "codextra-media-065148239936-ap-south-1-an.s3.ap-south-1.amazonaws.com",
        port: "",
        pathname: "/**",
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
      bodySizeLimit: 10 * 1024 * 1024, // Increase limit to 5 MB
      allowedOrigins: process.env.SERVER_ACTIONS_ALLOWED_ORIGINS
        ? process.env.SERVER_ACTIONS_ALLOWED_ORIGINS.split(",")
        : [],
    },
  },
};

export default nextConfig;
