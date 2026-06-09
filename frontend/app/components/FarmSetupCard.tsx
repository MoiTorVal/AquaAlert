"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import {
  createBaselineIrrigation,
  updateFarm,
  type Farm,
} from "../lib/api";

const dismissKey = (farmId: number) => `farm-setup-dismissed-${farmId}`;

/** Onboarding: baseline water use + pump profile. Skippable — savings need
 * these, alerts don't, so the card never blocks the page. */
export default function FarmSetupCard({
  farm,
  hasBaseline,
  onChanged,
}: {
  farm: Farm;
  hasBaseline: boolean;
  onChanged: () => void;
}) {
  const t = useTranslations("setup");
  const [dismissed, setDismissed] = useState(
    () =>
      typeof window !== "undefined" &&
      window.localStorage.getItem(dismissKey(farm.id)) === "1",
  );
  const [baselineGallons, setBaselineGallons] = useState("");
  const [pumpHp, setPumpHp] = useState(farm.pump_hp?.toString() ?? "");
  const [pumpLift, setPumpLift] = useState(farm.pump_lift_ft?.toString() ?? "");
  const [waterSource, setWaterSource] = useState(farm.water_source ?? "");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const needsPump = farm.pump_hp == null || farm.pump_lift_ft == null;
  if (dismissed || (hasBaseline && !needsPump)) return null;

  const skip = () => {
    window.localStorage.setItem(dismissKey(farm.id), "1");
    setDismissed(true);
  };

  const save = async () => {
    setError(null);
    setSaving(true);
    try {
      if (!hasBaseline && baselineGallons) {
        await createBaselineIrrigation(farm.id, Number(baselineGallons));
      }
      if (needsPump && (pumpHp || pumpLift || waterSource)) {
        await updateFarm(farm.id, {
          pump_hp: pumpHp ? Number(pumpHp) : null,
          pump_lift_ft: pumpLift ? Number(pumpLift) : null,
          water_source: (waterSource || null) as Farm["water_source"],
        });
      }
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const inputClass = "mt-1 w-full rounded-lg border border-gray-300 p-2";

  return (
    <section
      data-testid="farm-setup-card"
      className="rounded-2xl border border-blue-200 bg-blue-50 p-6"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{t("title")}</h2>
        <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
          {t("neededForSavings")}
        </span>
      </div>

      <div className="mt-4 flex flex-col gap-5 text-sm">
        {!hasBaseline && (
          <div>
            <h3 className="font-medium">{t("baselineHeading")}</h3>
            <p className="mt-1 text-gray-600">{t("baselineWhy")}</p>
            <label className="mt-2 block">
              <span className="text-gray-700">{t("baselineGallons")}</span>
              <input
                type="number"
                inputMode="decimal"
                value={baselineGallons}
                onChange={(e) => setBaselineGallons(e.target.value)}
                className={inputClass}
              />
            </label>
          </div>
        )}

        {needsPump && (
          <div>
            <h3 className="font-medium">{t("pumpHeading")}</h3>
            <p className="mt-1 text-gray-600">{t("pumpWhy")}</p>
            <div className="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <label>
                <span className="text-gray-700">{t("pumpHp")}</span>
                <input
                  type="number"
                  inputMode="decimal"
                  value={pumpHp}
                  onChange={(e) => setPumpHp(e.target.value)}
                  className={inputClass}
                />
              </label>
              <label>
                <span className="text-gray-700">{t("pumpLift")}</span>
                <input
                  type="number"
                  inputMode="decimal"
                  value={pumpLift}
                  onChange={(e) => setPumpLift(e.target.value)}
                  className={inputClass}
                />
              </label>
              <label>
                <span className="text-gray-700">{t("waterSource")}</span>
                <select
                  value={waterSource}
                  onChange={(e) => setWaterSource(e.target.value as typeof waterSource)}
                  className={inputClass}
                >
                  <option value="">—</option>
                  <option value="well">{t("well")}</option>
                  <option value="canal">{t("canal")}</option>
                  <option value="surface">{t("surface")}</option>
                </select>
              </label>
            </div>
          </div>
        )}

        {error && (
          <p role="alert" className="text-red-600">
            {error}
          </p>
        )}

        <div className="flex gap-3">
          <button
            onClick={save}
            disabled={saving}
            className="rounded-lg bg-green-600 px-4 py-2 font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            {t("save")}
          </button>
          <button
            onClick={skip}
            className="rounded-lg px-4 py-2 text-gray-600 hover:bg-gray-100"
          >
            {t("skip")}
          </button>
        </div>
      </div>
    </section>
  );
}
