"use client";

import { useId, useState } from "react";
import { useTranslations } from "next-intl";

// Message keys under "glossary" in messages/{locale}.json
export const GLOSSARY_TERMS = [
  "VWC",
  "FieldCapacity",
  "MAD",
  "ET",
  "PAW",
  "RAW",
  "WaterDeficit",
] as const;

export type GlossaryTerm = (typeof GLOSSARY_TERMS)[number];

export default function GlossaryTooltip({ term }: { term: GlossaryTerm }) {
  const t = useTranslations("glossary");
  const [open, setOpen] = useState(false);
  const tooltipId = useId();

  return (
    <span className="relative inline-block">
      <button
        type="button"
        aria-label={t("ariaLabel", { term })}
        aria-expanded={open}
        aria-describedby={open ? tooltipId : undefined}
        onClick={() => setOpen((v) => !v)}
        onBlur={() => setOpen(false)}
        className="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full border border-gray-300 text-[10px] text-gray-500 hover:bg-gray-100"
      >
        ?
      </button>
      {open && (
        <span
          id={tooltipId}
          role="tooltip"
          className="absolute left-1/2 z-10 mt-1 w-56 -translate-x-1/2 rounded-lg bg-gray-900 p-2 text-xs text-white shadow-lg"
        >
          {t(term)}
        </span>
      )}
    </span>
  );
}
