import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const isDev = process.env.NODE_ENV === "development";
const apiOrigin =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Config-based CSP (no nonces): nonce CSP forces dynamic rendering on every
// page (see node_modules/next/dist/docs/01-app/02-guides/content-security-policy.md)
// and we ship zero third-party scripts. script-src 'unsafe-inline' is the
// trade-off — Next injects inline hydration scripts; revisit with nonces or
// SRI if third-party scripts ever land.
const csp = [
  "default-src 'self'",
  // dev needs unsafe-eval: React rebuilds server error stacks via eval
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  // framer-motion and Leaflet position elements via inline style attributes
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' blob: data: https://server.arcgisonline.com https://images.unsplash.com",
  "font-src 'self'",
  `connect-src 'self' ${apiOrigin} https://formspree.io`,
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  // would upgrade dev's http API calls to https and break them
  ...(isDev ? [] : ["upgrade-insecure-requests"]),
].join("; ");

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [{ hostname: "images.unsplash.com" }],
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "Content-Security-Policy", value: csp },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

const withNextIntl = createNextIntlPlugin();

export default withNextIntl(nextConfig);
