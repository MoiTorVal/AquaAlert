"use client";

import { useLocale, useTranslations } from "next-intl";
import type { StressSeverity, WaterStress } from "../lib/api";
import { formatDate } from "../lib/format";

const SEVERITY_STYLES: Record<StressSeverity, { dot: string; bg: string }> = {
  green: { dot: "bg-green-500", bg: "bg-green-50 border-green-200" },
  yellow: { dot: "bg-yellow-400", bg: "bg-yellow-50 border-yellow-300" },
  red: { dot: "bg-red-500", bg: "bg-red-50 border-red-300" },
};

const SEVERITY_LABEL_KEY = {
  green: "healthy",
  yellow: "approaching",
  red: "stressed",
} as const;

export default function TrafficLightCard({ stress }: { stress: WaterStress }) {
  const t = useTranslations("trafficLight");
  const locale = useLocale();
  const style = stress.severity ? SEVERITY_STYLES[stress.severity] : null;
  const days = stress.days_to_stress;

  const message = (() => {
    switch (stress.severity) {
      case "red":
        return t("redMessage");
      case "yellow":
        return days != null
          ? t("yellowMessageDays", { days })
          : t("yellowMessage");
      case "green":
        return days != null
          ? t("greenMessageDays", { days })
          : t("greenMessage");
      default:
        return t("unknownMessage");
    }
  })();

  return (
    <section
      data-testid="traffic-light"
      className={`rounded-2xl border p-6 ${style?.bg ?? "bg-gray-50 border-gray-200"}`}
    >
      <div className="flex items-center gap-3">
        <span
          aria-hidden
          className={`h-5 w-5 rounded-full ${style?.dot ?? "bg-gray-300"}`}
        />
        <h2 className="text-lg font-semibold">
          {stress.severity
            ? t(SEVERITY_LABEL_KEY[stress.severity])
            : t("noAssessment")}
        </h2>
      </div>
      <p className="mt-2 text-gray-700">{message}</p>
      <p className="mt-3 text-xs text-gray-500">
        {t("asOf", { date: formatDate(stress.as_of_date, locale) })}
        {stress.et_is_stale && (
          <span
            role="status"
            className="ml-2 rounded bg-amber-100 px-2 py-0.5 font-medium text-amber-800"
          >
            {t("staleBanner")}
          </span>
        )}
      </p>
    </section>
  );
}
