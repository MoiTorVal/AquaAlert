"use client";

import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { updateMe } from "../lib/api";
import { useAuth } from "../context/AuthContext";

const LOCALES = [
  { code: "en", label: "EN" },
  { code: "es", label: "ES" },
] as const;

function setLocaleCookie(code: string) {
  document.cookie = `NEXT_LOCALE=${code}; path=/; max-age=31536000; samesite=lax`;
}

export default function LocaleToggle() {
  const locale = useLocale();
  const router = useRouter();
  const { user } = useAuth();

  const switchTo = (code: "en" | "es") => {
    if (code === locale) return;
    setLocaleCookie(code);
    if (user) {
      // best-effort: cookie already switched the UI; profile sync can fail quietly
      updateMe({ locale: code }).catch(() => {});
    }
    router.refresh();
  };

  return (
    <div
      role="group"
      aria-label="Language"
      className="flex items-center rounded-lg border border-white/20 text-xs"
    >
      {LOCALES.map(({ code, label }) => (
        <button
          key={code}
          onClick={() => switchTo(code)}
          aria-pressed={locale === code}
          lang={code}
          className={`px-2 py-1 transition-colors ${
            locale === code
              ? "bg-white/20 text-white"
              : "text-white/60 hover:text-white"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
