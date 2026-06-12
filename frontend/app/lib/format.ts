/** Display formatting for raw API values (dates, lowercase user input). */

/** "2026-03-25" → "Mar 25, 2026" (en) / "25 mar 2026" (es). Null-safe. */
export function formatDate(iso: string | null, locale: string): string {
  if (!iso) return "—";
  // Date-only strings parse as UTC midnight; format in UTC so the date
  // never shifts a day in western timezones.
  const parsed = new Date(`${iso.slice(0, 10)}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) return iso;
  return new Intl.DateTimeFormat(locale, {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(parsed);
}

/** Capitalizes each word for display ("moi's farm" → "Moi's Farm") without
 * touching the stored value or already-capitalized input ("USDA" stays). */
export function displayName(value: string | null): string {
  if (!value) return "—";
  return value.replace(
    /(^|\s)(\p{Ll})/gu,
    (_, sep: string, ch: string) => sep + ch.toUpperCase(),
  );
}
