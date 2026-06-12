"use client";

import { useLocale, useTranslations } from "next-intl";
import type { WaterSavingsRow } from "../lib/api";
import { formatDate } from "../lib/format";

export default function SavingsCard({ rows }: { rows: WaterSavingsRow[] }) {
  const t = useTranslations("savings");
  const locale = useLocale();
  const nf = new Intl.NumberFormat(locale, { maximumFractionDigits: 0 });
  const nf1 = new Intl.NumberFormat(locale, { maximumFractionDigits: 1 });

  if (rows.length === 0) {
    return (
      <section className="rounded-2xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold">{t("title")}</h2>
        <p className="mt-2 text-sm text-gray-500">{t("empty")}</p>
      </section>
    );
  }

  const gallons = rows.reduce((sum, r) => sum + r.gallons_saved, 0);
  const kwh = rows.reduce((sum, r) => sum + r.kwh_saved, 0);
  const co2 = rows.reduce((sum, r) => sum + r.co2_kg_saved, 0);
  // rows is non-empty here; reduce without an initial value is safe
  const asOf = rows
    .map((r) => r.period_end)
    .reduce((a, b) => (a > b ? a : b));

  return (
    <section
      data-testid="savings-card"
      className="rounded-2xl border border-gray-200 p-6"
    >
      <h2 className="text-lg font-semibold">{t("titleSeason")}</h2>
      <p className="mt-2 text-2xl font-bold text-green-700">
        {t("galSaved", { gallons: nf.format(gallons) })}
      </p>
      <p className="mt-1 text-sm text-gray-600">
        {t("energyLine", { kwh: nf1.format(kwh), co2: nf1.format(co2) })}
      </p>
      <p className="mt-3 text-xs text-gray-500">
        {t("asOf", { date: formatDate(asOf, locale) })}
      </p>
    </section>
  );
}
