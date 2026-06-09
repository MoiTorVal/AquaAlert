"use client";

import { useLocale, useTranslations } from "next-intl";
import type { WaterSavingsRow } from "../lib/api";

const W = 640;
const H = 220;
const PAD = { top: 12, right: 8, bottom: 28, left: 8 };

/** Weekly gallons-saved bars with a cumulative overlay line.
 * Hand-rolled SVG: two simple series don't justify a chart dependency. */
export default function WeeklySavingsChart({ rows }: { rows: WaterSavingsRow[] }) {
  const t = useTranslations("savingsPage");
  const locale = useLocale();
  const nf = new Intl.NumberFormat(locale, { maximumFractionDigits: 0 });

  if (rows.length === 0) return null;

  const sorted = [...rows].sort((a, b) =>
    a.period_start.localeCompare(b.period_start),
  );
  const cumulative: number[] = [];
  sorted.reduce((sum, r) => {
    const next = sum + r.gallons_saved;
    cumulative.push(next);
    return next;
  }, 0);

  const maxBar = Math.max(...sorted.map((r) => Math.abs(r.gallons_saved)), 1);
  const maxCum = Math.max(...cumulative.map(Math.abs), 1);
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const slot = innerW / sorted.length;
  const barW = Math.min(slot * 0.6, 48);
  const zeroY = PAD.top + innerH / 2;

  const barY = (v: number) => (v >= 0 ? zeroY - (v / maxBar) * (innerH / 2) : zeroY);
  const barH = (v: number) => (Math.abs(v) / maxBar) * (innerH / 2);
  const cumPoint = (v: number, i: number) =>
    `${PAD.left + slot * i + slot / 2},${zeroY - (v / maxCum) * (innerH / 2)}`;

  return (
    <figure data-testid="weekly-savings-chart">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={t("chartAria")}
        className="w-full"
      >
        <line x1={PAD.left} y1={zeroY} x2={W - PAD.right} y2={zeroY} stroke="#d1d5db" />
        {sorted.map((r, i) => (
          <g key={r.id}>
            <rect
              x={PAD.left + slot * i + (slot - barW) / 2}
              y={barY(r.gallons_saved)}
              width={barW}
              height={barH(r.gallons_saved)}
              rx={3}
              className={r.gallons_saved >= 0 ? "fill-green-500" : "fill-red-400"}
            >
              <title>{`${r.period_start}: ${nf.format(r.gallons_saved)} gal`}</title>
            </rect>
            <text
              x={PAD.left + slot * i + slot / 2}
              y={H - 8}
              textAnchor="middle"
              className="fill-gray-400 text-[9px]"
            >
              {r.period_start.slice(5)}
            </text>
          </g>
        ))}
        <polyline
          points={cumulative.map(cumPoint).join(" ")}
          fill="none"
          stroke="#166534"
          strokeWidth={2}
        />
      </svg>
      <figcaption className="mt-1 text-xs text-gray-500">
        {t("chartCaption")}
      </figcaption>
    </figure>
  );
}
