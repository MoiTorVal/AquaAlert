"use client";

import { useEffect, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { getImpactStats, type ImpactStats } from "../lib/api";

type LoadState =
  | { status: "loading" }
  | { status: "error" }
  | { status: "ready"; stats: ImpactStats | null };

/** Public — no login. Aggregates only; backend suppresses cohorts under 3 farms. */
export default function ImpactPage() {
  const t = useTranslations("impact");
  const locale = useLocale();
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    getImpactStats()
      .then((stats) => active && setState({ status: "ready", stats }))
      .catch(() => active && setState({ status: "error" }));
    return () => {
      active = false;
    };
  }, []);

  if (state.status === "loading")
    return (
      <main className="mx-auto max-w-3xl p-6">
        <div className="mt-8 h-48 animate-pulse rounded-2xl bg-gray-100" />
      </main>
    );

  const stats = state.status === "ready" ? state.stats : null;
  const nf = new Intl.NumberFormat(locale, { maximumFractionDigits: 0 });

  return (
    <main className="mx-auto max-w-3xl p-6 pt-28">
      <h1 className="text-3xl font-bold">{t("title")}</h1>
      <p className="mt-2 text-gray-600">{t("subtitle")}</p>

      {stats ? (
        <>
          <section className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Big label={t("gallonsSaved")} value={nf.format(stats.total_gallons_saved)} />
            <Big label={t("kwhSaved")} value={nf.format(stats.total_kwh_saved)} />
            <Big label={t("co2Avoided")} value={nf.format(stats.total_co2_kg_saved)} />
          </section>

          <section className="mt-6 rounded-2xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold">
              {t("farmsMonitored", { count: stats.total_farms })}
            </h2>
            <div className="mt-3 flex gap-4 text-sm">
              <Dot color="bg-green-500" label={t("green", { count: stats.farms_green })} />
              <Dot color="bg-yellow-400" label={t("yellow", { count: stats.farms_yellow })} />
              <Dot color="bg-red-500" label={t("red", { count: stats.farms_red })} />
            </div>
          </section>

          <p className="mt-4 text-xs text-gray-500">
            {t("asOf", { date: stats.snapshot_date })} · {t("privacyNote")}
          </p>
        </>
      ) : (
        <section className="mt-8 rounded-2xl border border-gray-200 bg-gray-50 p-8 text-center">
          <h2 className="text-lg font-semibold">{t("comingSoonTitle")}</h2>
          <p className="mt-2 text-sm text-gray-600">{t("comingSoonBody")}</p>
        </section>
      )}
    </main>
  );
}

function Big({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-gray-200 p-6 text-center">
      <div className="text-3xl font-bold text-green-700">{value}</div>
      <div className="mt-1 text-sm text-gray-500">{label}</div>
    </div>
  );
}

function Dot({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span aria-hidden className={`h-3 w-3 rounded-full ${color}`} />
      {label}
    </span>
  );
}
