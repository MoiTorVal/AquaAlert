"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { updateMe } from "../lib/api";

type Answer = boolean | null;

function TriChoice({
  legend,
  value,
  onChange,
  labels,
}: {
  legend: string;
  value: Answer;
  onChange: (v: Answer) => void;
  labels: { yes: string; no: string; preferNot: string };
}) {
  const options: { label: string; v: Answer }[] = [
    { label: labels.yes, v: true },
    { label: labels.no, v: false },
    { label: labels.preferNot, v: null },
  ];
  return (
    <fieldset className="mt-4">
      <legend className="text-sm font-medium text-gray-800">{legend}</legend>
      <div className="mt-2 flex gap-2">
        {options.map(({ label, v }) => (
          <button
            key={label}
            type="button"
            aria-pressed={value === v}
            onClick={() => onChange(v)}
            className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
              value === v
                ? "border-green-600 bg-green-50 text-green-800"
                : "border-gray-300 text-gray-600 hover:bg-gray-50"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

/** Post-signup equity self-ID. Voluntary by design (CLAUDE.md invariant):
 * plain-language why, explicit skip, "prefer not to say" stores null. */
export default function WelcomePage() {
  const t = useTranslations("equity");
  const router = useRouter();
  const [disadvantaged, setDisadvantaged] = useState<Answer>(null);
  const [beginning, setBeginning] = useState<Answer>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const labels = {
    yes: t("yes"),
    no: t("no"),
    preferNot: t("preferNot"),
  };

  const finish = () => router.push("/farms");

  const save = async () => {
    setError(null);
    setSaving(true);
    try {
      await updateMe({
        is_socially_disadvantaged: disadvantaged,
        is_beginning_farmer: beginning,
      });
      finish();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
      setSaving(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-[70vh] max-w-lg flex-col justify-center p-6">
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      <p className="mt-3 text-sm text-gray-600">{t("why")}</p>

      <TriChoice
        legend={t("sociallyDisadvantaged")}
        value={disadvantaged}
        onChange={setDisadvantaged}
        labels={labels}
      />
      <TriChoice
        legend={t("beginningFarmer")}
        value={beginning}
        onChange={setBeginning}
        labels={labels}
      />

      {error && (
        <p role="alert" className="mt-4 text-sm text-red-600">
          {error}
        </p>
      )}

      <div className="mt-8 flex gap-3">
        <button
          onClick={save}
          disabled={saving}
          className="rounded-lg bg-green-600 px-5 py-2.5 font-medium text-white hover:bg-green-700 disabled:opacity-50"
        >
          {t("save")}
        </button>
        <button
          onClick={finish}
          className="rounded-lg px-5 py-2.5 text-gray-600 hover:bg-gray-100"
        >
          {t("skip")}
        </button>
      </div>
    </main>
  );
}
