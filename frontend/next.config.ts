import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    remotePatterns: [{ hostname: "images.unsplash.com" }],
  },

  redirects: async () => [
    { source: "/farms/:id", destination: "/farms", permanent: false },
  ],
};

export default nextConfig;
