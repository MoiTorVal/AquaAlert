"use client";

import { use, useEffect, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  ApiError,
  getAlerts,
  getBaselineIrrigations,
  getEtSeries,
  getFarm,
  getIrrigationEvents,
  getWaterSavings,
  getWaterStress,
  getWeatherReadings,
  type Alert,
  type Farm,
  type IrrigationEvent,
  type WaterSavingsRow,
  type WaterStress,
} from "../../lib/api";
import { displayName, formatDate, isoAddDays } from "../../lib/format";
import { AWC_IN_PER_FT, gallonsToAcreInches } from "../../lib/soil";
import TrafficLightCard from "../../components/TrafficLightCard";
import StressDetails from "../../components/StressDetails";
import SavingsCard from "../../components/SavingsCard";
import IrrigationLogSheet from "../../components/IrrigationLogSheet";
import EditFarmSheet from "../../components/EditFarmSheet";
import FarmSetupCard from "../../components/FarmSetupCard";
import PendingAssessmentCard from "../../components/PendingAssessmentCard";
import AlertsCard from "../../components/AlertsCard";
import ProtectedRoute from "../../components/ProtectedRoute";

// Leaflet requires `window`; load client-side only (see FieldMap.tsx).
const FieldMap = dynamic(() => import("../../components/FieldMap"), {
  ssr: false,
  loading: () => <div className="h-64 animate-pulse rounded-xl bg-gray-100" />,
});

const EVENTS_PREVIEW_COUNT = 5;

type LoadState =
  | { status: "loading" }
  | { status: "not-found" }
  | { status: "error"; message: string }
  | {
      status: "ready";
      farm: Farm;
      stress: WaterStress | null;
      savings: WaterSavingsRow[];
      hasBaseline: boolean;
      events: IrrigationEvent[];
      alerts: Alert[];
      // Oldest event_date that still counts as "this week", fixed at fetch
      // time (render must stay pure — no Date.now() there).
      weekCutoff: string;
      // 7-day cumulative crop ET in inches + its as-of date (cache-only
      // read — never spends an OpenET request). Null = no cached ET.
      et7In: number | null;
      etAsOf: string | null;
      // Trailing-7-day rainfall in inches for the pending hero. Null = no
      // cached weather rows.
      rain7In: number | null;
    };

export default function FarmDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <ProtectedRoute>
      <FarmDetailContent params={params} />
    </ProtectedRoute>
  );
}

function FarmDetailContent({ params }: { params: Promise<{ id: string }> }) {
  const t = useTranslations("farmDetail");
  const tSoil = useTranslations("soil");
  const locale = useLocale();
  const { id } = use(params);
  const farmId = Number(id);
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [logOpen, setLogOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [showAllEvents, setShowAllEvents] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = () => {
    setState({ status: "loading" });
    setReloadKey((k) => k + 1);
  };

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [farm, stress, savings, baselines, events, alerts] =
          await Promise.all([
            getFarm(farmId),
            getWaterStress(farmId),
            getWaterSavings(farmId),
            getBaselineIrrigations(farmId),
            getIrrigationEvents(farmId),
            getAlerts(farmId),
          ]);
        const weekCutoff = new Date(Date.now() - 6 * 86_400_000)
          .toISOString()
          .slice(0, 10);

        // Optional extras — failures here must never fail the page.
        let et7In: number | null = null;
        let etAsOf: string | null = null;
        let rain7In: number | null = null;
        if (stress?.et_latest_date != null) {
          try {
            const series = await getEtSeries(
              farmId,
              isoAddDays(stress.et_latest_date, -6),
              stress.et_latest_date,
            );
            if (series.results.length > 0) {
              et7In =
                series.results.reduce((sum, r) => sum + r.et_mm, 0) / 25.4;
              etAsOf = series.as_of;
            }
          } catch {}
        } else {
          // Pending farms: show cached local rainfall in the hero instead.
          try {
            const weather = await getWeatherReadings(
              farmId,
              `${weekCutoff}T00:00:00Z`,
            );
            const rains = weather
              .map((w) => w.rainfall_mm)
              .filter((v): v is number => v != null);
            if (rains.length > 0) {
              rain7In = rains.reduce((sum, v) => sum + v, 0) / 25.4;
            }
          } catch {}
        }

        if (active)
          setState({
            status: "ready",
            farm,
            stress,
            savings,
            hasBaseline: baselines.length > 0,
            events,
            alerts,
            weekCutoff,
            et7In,
            etAsOf,
            rain7In,
          });
      } catch (err) {
        if (!active) return;
        if (err instanceof ApiError && err.status === 404) {
          setState({ status: "not-found" });
        } else {
          setState({
            status: "error",
            message: err instanceof Error ? err.message : String(err),
          });
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [farmId, reloadKey]);

  if (state.status === "loading") return <DetailSkeleton />;
  if (state.status === "not-found")
    return (
      <CenteredMessage title={t("notFound")}>
        <Link href="/farms" className="text-green-700 hover:underline">
          {t("backToFarms")}
        </Link>
      </CenteredMessage>
    );
  if (state.status === "error")
    return (
      <CenteredMessage title={t("errorTitle")}>
        <p className="text-sm text-red-500">{state.message}</p>
        <button
          onClick={reload}
          className="mt-4 rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50"
        >
          {t("tryAgain")}
        </button>
      </CenteredMessage>
    );

  const {
    farm,
    stress,
    savings,
    hasBaseline,
    events,
    alerts,
    weekCutoff,
    et7In,
    etAsOf,
    rain7In,
  } = state;

  // Gallons applied over the trailing 7 days, for the irrigation subtotal.
  const weekGallons = events
    .filter((e) => e.event_date >= weekCutoff)
    .reduce((sum, e) => sum + e.gallons_applied, 0);
  const weekAcIn = gallonsToAcreInches(weekGallons);
  const visibleEvents = showAllEvents
    ? events
    : events.slice(0, EVENTS_PREVIEW_COUNT);

  return (
    // pt-28 clears the fixed navbar (matches /impact)
    <main className="mx-auto max-w-6xl p-6 pt-28">
      <Link href="/farms" className="text-sm text-gray-500 hover:underline">
        {t("back")}
      </Link>
      <div className="mt-2 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{displayName(farm.name)}</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setEditOpen(true)}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            {t("edit")}
          </button>
          <button
            onClick={() => setLogOpen(true)}
            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
          >
            {t("logIrrigation")}
          </button>
        </div>
      </div>

      <div className="mt-6 flex flex-col gap-4">
        <FarmSetupCard farm={farm} hasBaseline={hasBaseline} onChanged={reload} />

        <div className="grid gap-4 lg:grid-cols-5 lg:items-start">
          <div className="flex flex-col gap-4 lg:col-span-3">
            {stress ? (
              <>
                <TrafficLightCard stress={stress} />
                <StressDetails stress={stress} farm={farm} />
              </>
            ) : (
              <PendingAssessmentCard
                farm={farm}
                rain7In={rain7In}
                onAddDetails={() => setEditOpen(true)}
              />
            )}

            <AlertsCard alerts={alerts} />

            <Link href={`/farms/${farmId}/savings`} className="block">
              <SavingsCard rows={savings} />
            </Link>
          </div>

          <div className="flex flex-col gap-4 lg:col-span-2">
            <section className="rounded-2xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold">{t("field")}</h2>
              {farm.field_polygon ? (
                <div className="mt-4">
                  <FieldMap
                    wkt={farm.field_polygon}
                    label={
                      farm.acreage_acres != null
                        ? t("acresChip", {
                            acres: farm.acreage_acres.toLocaleString(),
                          })
                        : undefined
                    }
                  />
                </div>
              ) : (
                <div className="mt-4 rounded-xl bg-gray-50 p-4 text-sm text-gray-600">
                  <p>{t("noBoundary")}</p>
                  <button
                    onClick={() => setEditOpen(true)}
                    className="mt-3 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
                  >
                    {t("drawBoundary")}
                  </button>
                </div>
              )}
              {et7In != null && etAsOf != null && (
                <div className="mt-4 flex items-baseline justify-between rounded-lg bg-blue-50 px-3 py-2 text-sm">
                  <span className="text-gray-600">{t("etReadout")}</span>
                  <span className="font-semibold text-gray-900">
                    {t("etValue", { inches: et7In.toFixed(2) })}{" "}
                    <span className="text-xs font-normal text-gray-500">
                      {t("etAsOf", { date: formatDate(etAsOf, locale) })}
                    </span>
                  </span>
                </div>
              )}
              <dl className="mt-4 grid grid-cols-3 gap-2">
                <FieldFact
                  label={t("crop")}
                  value={farm.crop_type ? displayName(farm.crop_type) : "—"}
                />
                <FieldFact
                  label={t("planted")}
                  value={formatDate(farm.planting_date, locale)}
                />
                <FieldFact
                  label={t("soil")}
                  value={farm.soil_type ? tSoil(farm.soil_type) : "—"}
                  sub={
                    farm.soil_type
                      ? t("holdsWater", { awc: AWC_IN_PER_FT[farm.soil_type] })
                      : undefined
                  }
                />
              </dl>
            </section>

            <section className="rounded-2xl border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">
                  {t("irrigationHistory")}
                </h2>
                {weekGallons > 0 && (
                  <span className="rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
                    {t("thisWeek", { gallons: weekGallons.toLocaleString() })}
                    {weekAcIn >= 0.01 &&
                      ` · ${t("acInWeek", { acin: weekAcIn.toFixed(2) })}`}
                  </span>
                )}
              </div>
              {events.length === 0 ? (
                <div className="mt-2 text-sm text-gray-500">
                  <p>{t("noIrrigations")}</p>
                  <button
                    onClick={() => setLogOpen(true)}
                    className="mt-3 rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    {t("logIrrigation")}
                  </button>
                </div>
              ) : (
                <>
                  <ul className="mt-3 divide-y divide-gray-100 text-sm">
                    {visibleEvents.map((event) => (
                      <li
                        key={event.id}
                        className="flex items-center justify-between py-2"
                      >
                        <span className="text-gray-600">
                          {formatDate(event.event_date, locale)}
                        </span>
                        <span className="flex items-center gap-2">
                          {event.source === "estimated" && (
                            <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                              {t("estimated")}
                            </span>
                          )}
                          {event.hours_run != null && event.pump_gpm != null && (
                            <span className="text-xs text-gray-500">
                              {t("runtimeValue", {
                                hours: event.hours_run.toLocaleString(),
                                gpm: event.pump_gpm.toLocaleString(),
                              })}
                            </span>
                          )}
                          <span className="font-medium">
                            {t("gallonsValue", {
                              gallons: event.gallons_applied.toLocaleString(),
                            })}
                          </span>
                        </span>
                      </li>
                    ))}
                  </ul>
                  {events.length > EVENTS_PREVIEW_COUNT && (
                    <button
                      onClick={() => setShowAllEvents((v) => !v)}
                      className="mt-3 text-sm font-medium text-green-700 hover:underline"
                    >
                      {showAllEvents
                        ? t("showLess")
                        : t("viewAll", { count: events.length })}
                    </button>
                  )}
                </>
              )}
            </section>
          </div>
        </div>
      </div>

      <IrrigationLogSheet
        farmId={farmId}
        open={logOpen}
        onClose={() => setLogOpen(false)}
        onLogged={reload}
      />
      {editOpen && (
        <EditFarmSheet
          farm={farm}
          onClose={() => setEditOpen(false)}
          onSaved={reload}
        />
      )}
    </main>
  );
}

function FieldFact({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-lg bg-gray-50 p-3">
      <dt className="text-xs text-gray-500">{label}</dt>
      <dd className="mt-0.5 text-sm font-semibold text-gray-900">{value}</dd>
      {sub && <dd className="mt-0.5 text-xs text-gray-500">{sub}</dd>}
    </div>
  );
}

function DetailSkeleton() {
  return (
    <main className="mx-auto max-w-6xl p-6 pt-28">
      <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
      <div className="mt-6 grid gap-4 lg:grid-cols-5">
        <div className="flex flex-col gap-4 lg:col-span-3">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-40 animate-pulse rounded-2xl bg-gray-100" />
          ))}
        </div>
        <div className="lg:col-span-2">
          <div className="h-80 animate-pulse rounded-2xl bg-gray-100" />
        </div>
      </div>
    </main>
  );
}

function CenteredMessage({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-3xl flex-col items-center justify-center p-6 text-center">
      <h1 className="mb-3 text-xl font-semibold">{title}</h1>
      {children}
    </main>
  );
}
