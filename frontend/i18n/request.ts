import { getRequestConfig } from "next-intl/server";
import { cookies } from "next/headers";

// Locale comes from a cookie, not the URL — the app lives behind a login so
// localized URLs buy nothing. The header toggle sets the cookie and persists
// the choice to the user profile (User.locale) for cross-device consistency.
export const LOCALE_COOKIE = "NEXT_LOCALE";

export default getRequestConfig(async () => {
  const store = await cookies();
  const cookieLocale = store.get(LOCALE_COOKIE)?.value;
  const locale = cookieLocale === "es" ? "es" : "en";
  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
