"use client";

import { use, useEffect, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import {
  fetchSgmaReportBlobUrl,
  getSavingsSeries,
  type SavingsSeries,
} from "../../../lib/api";
import WeeklySavingsChart from "../../../components/WeeklySavingsChart";

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; series: SavingsSeries };

export default function SavingsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const t = useTranslations("savingsPage");
  const locale = useLocale();
  const { id } = use(params);
  const farmId = Number(id);
  const year = new Date().getFullYear();
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [exportError, setExportError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const series = await getSavingsSeries(
          farmId,
          `${year}-01-01`,
          `${year}-12-31`,
        );
        if (active) setState({ status: "ready", series });
      } catch (err) {
        if (active)
          setState({
            status: "error",
            message: err instanceof Error ? err.message : String(err),
          });
      }
    })();
    return () => {
      active = false;
    };
  }, [farmId, year]);

  const download = async (format: "csv" | "pdf") => {
    setExportError(null);
    setExporting(true);
    try {
      const url = await fetchSgmaReportBlobUrl(farmId, year, format);
      const a = document.createElement("a");
      a.href = url;
      a.download = `sgma-report-${year}-farm-${farmId}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : String(err));
    } finally {
      setExporting(false);
    }
  };

  if (state.status === "loading")
    return (
      <main className="mx-auto max-w-3xl p-6 pt-28">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
        <div className="mt-6 h-64 animate-pulse rounded-2xl bg-gray-100" />
      </main>
    );

  if (state.status === "error")
    return (
      <main className="mx-auto max-w-3xl p-6 pt-28 text-center">
        <h1 className="text-xl font-semibold">{t("errorTitle")}</h1>
        <p className="mt-2 text-sm text-red-500">{state.message}</p>
      </main>
    );

  const { series } = state;
  const nf = new Intl.NumberFormat(locale, { maximumFractionDigits: 0 });
  const nf1 = new Intl.NumberFormat(locale, { maximumFractionDigits: 1 });

  return (
    <main className="mx-auto max-w-3xl p-6 pt-28">
      <Link href={`/farms/${farmId}`} className="text-sm text-gray-500 hover:underline">
        {t("back")}
      </Link>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">{t("title", { year })}</h1>
        <div className="flex gap-2">
          <button
            onClick={() => download("pdf")}
            disabled={exporting}
            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            {t("downloadSgma")}
          </button>
          <button
            onClick={() => download("csv")}
            disabled={exporting}
            className="rounded-lg border px-4 py-2 text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            CSV
          </button>
        </div>
      </div>
      {exportError && (
        <p role="alert" className="mt-2 text-sm text-red-600">
          {exportError}
        </p>
      )}

      <section className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Stat label={t("totalSaved")} value={`${nf.format(series.totals.gallons_saved)} gal`} />
        <Stat label={t("energySaved")} value={`${nf1.format(series.totals.kwh_saved)} kWh`} />
        <Stat label={t("co2Avoided")} value={`${nf1.format(series.totals.co2_kg_saved)} kg`} />
      </section>

      <section className="mt-6 rounded-2xl border border-gray-200 p-6">
        {series.results.length > 0 ? (
          <WeeklySavingsChart rows={series.results} />
        ) : (
          <p className="text-sm text-gray-500">{t("empty")}</p>
        )}
      </section>

      <p className="mt-4 text-xs text-gray-500">
        {t("asOf", { date: series.end_date })}
      </p>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-gray-200 p-4">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="mt-1 text-xl font-bold text-green-700">{value}</div>
    </div>
  );
}
