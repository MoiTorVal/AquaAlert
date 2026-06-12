"use client";

import { useLocale, useTranslations } from "next-intl";
import type { Farm, WaterStress } from "../lib/api";
import { formatDate } from "../lib/format";
import GlossaryTooltip, { type GlossaryTerm } from "./GlossaryTooltip";

function Row({
  label,
  term,
  value,
}: {
  label: string;
  term?: GlossaryTerm;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between border-b border-gray-100 py-2 text-sm last:border-0">
      <dt className="flex items-center text-gray-600">
        {label}
        {term && <GlossaryTooltip term={term} />}
      </dt>
      <dd className="font-medium text-gray-900">{value}</dd>
    </div>
  );
}

const fmt = (v: number | null, unit: string) =>
  v == null ? "—" : `${v} ${unit}`;

export default function StressDetails({
  stress,
  farm,
}: {
  stress: WaterStress;
  farm: Farm;
}) {
  const t = useTranslations("stressDetails");
  const locale = useLocale();
  return (
    <details className="rounded-2xl border border-gray-200 p-4">
      <summary className="cursor-pointer text-sm font-medium text-gray-700">
        {t("summary")}
      </summary>
      <dl className="mt-3">
        <Row
          label={t("rootZoneMoisture")}
          term="VWC"
          value={fmt(stress.root_zone_moisture_pct, t("pctOfAvailable"))}
        />
        <Row
          label={t("fieldCapacity")}
          term="FieldCapacity"
          value={fmt(farm.field_capacity_pct, "%")}
        />
        <Row
          label={t("madThreshold")}
          term="MAD"
          value={fmt(stress.raw_threshold_mm, "mm")}
        />
        <Row
          label={t("waterDeficit")}
          term="WaterDeficit"
          value={fmt(stress.depletion_mm, "mm")}
        />
        <Row label={t("paw")} term="PAW" value={fmt(stress.paw_mm, "mm")} />
        <Row
          label={t("daysToStress")}
          value={
            stress.days_to_stress == null
              ? t("notApproaching")
              : t("daysValue", { days: stress.days_to_stress })
          }
        />
        <Row
          label={t("satelliteThrough")}
          term="ET"
          value={formatDate(stress.et_latest_date, locale)}
        />
      </dl>
    </details>
  );
}
