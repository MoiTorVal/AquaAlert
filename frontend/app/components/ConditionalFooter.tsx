"use client";

import { usePathname } from "next/navigation";
import Footer from "./Footer";

// Logged-in app screens shouldn't end in the marketing footer (login/demo
// links, brand pitch). Until the app grows a real route-group shell, gate it
// here by path prefix.
const APP_ROUTE_PREFIXES = ["/farms", "/welcome"];

export default function ConditionalFooter() {
  const pathname = usePathname();
  if (APP_ROUTE_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return null;
  }
  return <Footer />;
}
