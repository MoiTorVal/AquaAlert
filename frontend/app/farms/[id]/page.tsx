"use client";

import { use, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  ApiError,
  getBaselineIrrigations,
  getFarm,
  getIrrigationEvents,
  getWaterSavings,
  getWaterStress,
  type Farm,
  type IrrigationEvent,
  type WaterSavingsRow,
  type WaterStress,
} from "../../lib/api";
import { soilLabel } from "../../lib/validators";
import TrafficLightCard from "../../components/TrafficLightCard";
import StressDetails from "../../components/StressDetails";
import SavingsCard from "../../components/SavingsCard";
import IrrigationLogSheet from "../../components/IrrigationLogSheet";
import EditFarmSheet from "../../components/EditFarmSheet";
import FarmSetupCard from "../../components/FarmSetupCard";
import ProtectedRoute from "../../components/ProtectedRoute";

// Leaflet requires `window`; load client-side only (see FieldMap.tsx).
const FieldMap = dynamic(() => import("../../components/FieldMap"), {
  ssr: false,
  loading: () => <div className="h-64 animate-pulse rounded-xl bg-gray-100" />,
});

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
  const { id } = use(params);
  const farmId = Number(id);
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [logOpen, setLogOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = () => {
    setState({ status: "loading" });
    setReloadKey((k) => k + 1);
  };

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [farm, stress, savings, baselines, events] = await Promise.all([
          getFarm(farmId),
          getWaterStress(farmId),
          getWaterSavings(farmId),
          getBaselineIrrigations(farmId),
          getIrrigationEvents(farmId),
        ]);
        if (active)
          setState({
            status: "ready",
            farm,
            stress,
            savings,
            hasBaseline: baselines.length > 0,
            events,
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
          className="mt-4 rounded-lg border px-4 py-2 text-sm hover:bg-gray-50"
        >
          {t("tryAgain")}
        </button>
      </CenteredMessage>
    );

  const { farm, stress, savings, hasBaseline, events } = state;

  return (
    // pt-28 clears the fixed navbar (matches /impact)
    <main className="mx-auto max-w-3xl p-6 pt-28">
      <Link href="/farms" className="text-sm text-gray-500 hover:underline">
        {t("back")}
      </Link>
      <div className="mt-2 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{farm.name}</h1>
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
        {stress ? (
          <>
            <TrafficLightCard stress={stress} />
            <StressDetails stress={stress} farm={farm} />
          </>
        ) : (
          <section className="rounded-2xl border border-gray-200 bg-gray-50 p-6">
            <h2 className="text-lg font-semibold">{t("noAssessmentTitle")}</h2>
            <p className="mt-2 text-sm text-gray-600">{t("noAssessmentBody")}</p>
          </section>
        )}

        <section className="rounded-2xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold">{t("field")}</h2>
          {farm.field_polygon && (
            <div className="mt-4">
              <FieldMap wkt={farm.field_polygon} />
            </div>
          )}
          <dl className="mt-2 grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-gray-500">{t("crop")}</dt>
              <dd className="font-medium">{farm.crop_type ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-500">{t("planted")}</dt>
              <dd className="font-medium">{farm.planting_date ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-500">{t("soil")}</dt>
              <dd className="font-medium">
                {farm.soil_type ? soilLabel(farm.soil_type) : "—"}
              </dd>
            </div>
          </dl>
        </section>

        <section className="rounded-2xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold">{t("irrigationHistory")}</h2>
          {events.length === 0 ? (
            <p className="mt-2 text-sm text-gray-500">{t("noIrrigations")}</p>
          ) : (
            <ul className="mt-3 divide-y divide-gray-100 text-sm">
              {events.map((event) => (
                <li
                  key={event.id}
                  className="flex items-center justify-between py-2"
                >
                  <span className="text-gray-600">{event.event_date}</span>
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
          )}
        </section>

        <Link href={`/farms/${farmId}/savings`} className="block">
          <SavingsCard rows={savings} />
        </Link>
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

function DetailSkeleton() {
  return (
    <main className="mx-auto max-w-3xl p-6 pt-28">
      <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
      <div className="mt-6 flex flex-col gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-32 animate-pulse rounded-2xl bg-gray-100" />
        ))}
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
