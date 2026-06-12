"use client";

import { useTranslations } from "next-intl";
import type { Farm } from "../lib/api";

type ChecklistItem = {
  key: "boundary" | "crop" | "plantingDate" | "soil";
  done: boolean;
};

/** Hero shown while a farm has no water-stress assessment yet. Instead of a
 * bare empty box it shows setup progress and what happens next, with an
 * inline action for anything still missing. */
export default function PendingAssessmentCard({
  farm,
  onAddDetails,
  rain7In = null,
}: {
  farm: Farm;
  onAddDetails: () => void;
  /** Trailing-7-day rainfall in inches from cached weather; null = no data. */
  rain7In?: number | null;
}) {
  const t = useTranslations("pendingAssessment");

  const items: ChecklistItem[] = [
    { key: "boundary", done: farm.field_polygon != null },
    { key: "crop", done: farm.crop_type != null },
    { key: "plantingDate", done: farm.planting_date != null },
    { key: "soil", done: farm.soil_type != null },
  ];
  const missing = items.filter((item) => !item.done);
  const setupComplete = missing.length === 0;

  return (
    <section
      data-testid="pending-assessment"
      className="rounded-2xl border border-gray-200 bg-white p-6"
    >
      <div className="flex items-center gap-3">
        <span aria-hidden className="relative flex h-5 w-5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-gray-300 opacity-60" />
          <span className="relative inline-flex h-5 w-5 rounded-full bg-gray-300" />
        </span>
        <h2 className="text-lg font-semibold">
          {setupComplete ? t("waitingTitle") : t("setupTitle")}
        </h2>
      </div>
      <p className="mt-2 text-sm text-gray-600">
        {setupComplete ? t("waitingBody") : t("setupBody")}
      </p>

      <ul className="mt-4 flex flex-col gap-2 text-sm">
        {items.map((item) => (
          <li key={item.key} className="flex items-center gap-2">
            {item.done ? (
              <span aria-hidden className="text-green-600">
                ✓
              </span>
            ) : (
              <span aria-hidden className="text-gray-300">
                ○
              </span>
            )}
            <span className={item.done ? "text-gray-700" : "text-gray-500"}>
              {t(item.key)}
            </span>
          </li>
        ))}
        <li className="flex items-center gap-2">
          <span aria-hidden className="text-amber-500">
            ◌
          </span>
          <span className="text-gray-500">
            {setupComplete ? t("satellitePending") : t("satelliteBlocked")}
          </span>
        </li>
      </ul>

      {rain7In != null && (
        <p className="mt-4 rounded-lg bg-blue-50 px-3 py-2 text-sm text-gray-600">
          {t("rainLine", { inches: rain7In.toFixed(2) })}
        </p>
      )}

      {!setupComplete && (
        <button
          onClick={onAddDetails}
          className="mt-4 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
        >
          {t("addDetails")}
        </button>
      )}
    </section>
  );
}
