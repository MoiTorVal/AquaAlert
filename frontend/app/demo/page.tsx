import Link from "next/link";
import TrafficLightCard from "../components/TrafficLightCard";
import StressDetails from "../components/StressDetails";
import SavingsCard from "../components/SavingsCard";
import WeeklySavingsChart from "../components/WeeklySavingsChart";
import DemoFieldNdviMap from "../components/DemoFieldNdviMapClient";
import type { Farm, WaterSavingsRow, WaterStress } from "../lib/api";

export const metadata = {
  title: "Demo | AquaAlert",
  description: "Interactive AquaAlert product demo with realistic mock data",
};

const demoFarm = {
  id: 501,
  user_id: 1,
  name: "Yellowstone Ranch",
  location: "Fresno, CA",
  crop_type: "Pistachios",
  soil_type: "ClayLoam",
  root_depth_cm: 120,
  growth_stage: "midseason",
  planting_date: "2026-03-15",
  field_capacity_pct: 34,
  wilting_point_pct: 16,
  field_polygon: null,
  harvest_date: "2026-10-30",
  acreage_acres: 1000,
  pump_hp: 75,
  pump_lift_ft: 180,
  water_source: "well",
  created_at: "2026-02-01T00:00:00Z",
} satisfies Farm;

const demoStress = {
  id: 9001,
  farm_id: 501,
  as_of_date: "2026-06-12",
  depletion_mm: 82.4,
  root_zone_moisture_pct: 27.1,
  severity: "yellow",
  days_to_stress: 2,
  paw_mm: 148.2,
  raw_threshold_mm: 90,
  run_date: "2026-06-12T02:03:00Z",
  et_latest_date: "2026-06-09",
  et_is_stale: false,
} satisfies WaterStress;

const demoSavingsRows = [
  {
    id: 1,
    farm_id: 501,
    period_start: "2026-05-05",
    period_end: "2026-05-11",
    baseline_gallons: 98000,
    actual_gallons: 91000,
    gallons_saved: 7000,
    kwh_saved: 116.2,
    co2_kg_saved: 31.2,
    computed_at: "2026-05-12T03:00:00Z",
  },
  {
    id: 2,
    farm_id: 501,
    period_start: "2026-05-12",
    period_end: "2026-05-18",
    baseline_gallons: 98000,
    actual_gallons: 84500,
    gallons_saved: 13500,
    kwh_saved: 224.8,
    co2_kg_saved: 60.4,
    computed_at: "2026-05-19T03:00:00Z",
  },
  {
    id: 3,
    farm_id: 501,
    period_start: "2026-05-19",
    period_end: "2026-05-25",
    baseline_gallons: 98000,
    actual_gallons: 88300,
    gallons_saved: 9700,
    kwh_saved: 161.5,
    co2_kg_saved: 43.4,
    computed_at: "2026-05-26T03:00:00Z",
  },
  {
    id: 4,
    farm_id: 501,
    period_start: "2026-05-26",
    period_end: "2026-06-01",
    baseline_gallons: 98000,
    actual_gallons: 101000,
    gallons_saved: -3000,
    kwh_saved: -50.0,
    co2_kg_saved: -13.4,
    computed_at: "2026-06-02T03:00:00Z",
  },
  {
    id: 5,
    farm_id: 501,
    period_start: "2026-06-02",
    period_end: "2026-06-08",
    baseline_gallons: 98000,
    actual_gallons: 77200,
    gallons_saved: 20800,
    kwh_saved: 346.2,
    co2_kg_saved: 93.0,
    computed_at: "2026-06-09T03:00:00Z",
  },
] satisfies WaterSavingsRow[];

const demoFarms = [
  {
    name: "Yellowstone Ranch",
    status: "Approaching stress",
    crop: "Pistachios",
    location: "Fresno",
    acres: "1,000",
    date: "Planted Mar 15, 2026",
  },
  {
    name: "Moises Torres Valdez",
    status: "Healthy",
    crop: "Grapes",
    location: "Porterville",
    acres: "90",
    date: "Planted Apr 9, 2026",
  },
  {
    name: "Shmoi's Farms",
    status: "Pending first reading",
    crop: "Grapes",
    location: "Porterville",
    acres: "5",
    date: "Planned Jun 16, 2026",
  },
];

export default function DemoPage() {
  return (
    <main className="mx-auto max-w-7xl p-6 pt-28">
      <section className="rounded-2xl border border-green-200 bg-green-50 p-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-green-700">
          Portfolio demo
        </p>
        <h1 className="mt-2 text-3xl font-bold text-gray-900">
          AquaAlert full product walkthrough
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-gray-700">
          This page uses realistic mock data to show the full end-to-end
          experience: multi-farm monitoring, AquaCrop stress alerts, NDVI
          confirmation, one-tap irrigation logging, and water-savings reporting.
        </p>
        <div className="mt-4 flex flex-wrap gap-2 text-xs">
          {[
            "Satellite ET + AquaCrop stress model",
            "Escalation-only alerting",
            "SMS opt-in + feedback loop",
            "Weekly water/energy/CO₂ savings",
            "Public impact rollup",
          ].map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-white px-3 py-1 text-gray-700"
            >
              {tag}
            </span>
          ))}
        </div>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Link
            href="/login"
            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
          >
            Try demo login
          </Link>
          <Link
            href="/impact"
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            View public impact page
          </Link>
        </div>
      </section>

      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        <Stat title="Farms monitored" value="4" />
        <Stat title="Total acres" value="1,115" />
        <Stat title="Need attention today" value="1" accent />
      </section>

      <section className="mt-8 rounded-2xl border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900">Farm list view</h2>
        <p className="mt-1 text-sm text-gray-600">
          Fast scan of status across all farms before drilling into one field.
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[760px] text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500">
                <th className="py-2 pr-3 font-medium">Name</th>
                <th className="py-2 pr-3 font-medium">Status</th>
                <th className="py-2 pr-3 font-medium">Crop</th>
                <th className="py-2 pr-3 font-medium">Location</th>
                <th className="py-2 pr-3 text-right font-medium">Acres</th>
                <th className="py-2 pr-3 font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {demoFarms.map((farm) => (
                <tr key={farm.name} className="border-b border-gray-100">
                  <td className="py-3 pr-3 font-medium text-gray-900">
                    {farm.name}
                  </td>
                  <td className="py-3 pr-3 text-gray-700">{farm.status}</td>
                  <td className="py-3 pr-3 text-gray-700">{farm.crop}</td>
                  <td className="py-3 pr-3 text-gray-700">{farm.location}</td>
                  <td className="py-3 pr-3 text-right tabular-nums text-gray-700">
                    {farm.acres}
                  </td>
                  <td className="py-3 pr-3 text-gray-700">{farm.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-5">
        <div className="space-y-4 lg:col-span-3">
          <h2 className="text-xl font-semibold text-gray-900">
            Field detail: stress monitoring + explainability
          </h2>
          <DemoFieldNdviMap />
          <TrafficLightCard stress={demoStress} />
          <StressDetails stress={demoStress} farm={demoFarm} />

          <div className="rounded-2xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900">
              Alerts and NDVI confirmation
            </h3>
            <ul className="mt-3 divide-y divide-gray-100 text-sm">
              <li className="flex items-center justify-between py-2">
                <span className="font-medium text-gray-800">
                  Approaching stress — 2 days left
                </span>
                <span className="text-gray-500">Jun 12, 2026</span>
              </li>
              <li className="py-2 text-xs text-green-700">
                NDVI also shows stress (as of Jun 9, 2026)
              </li>
              <li className="py-2 text-xs text-gray-600">
                Farmer feedback: “Confirmed in field”
              </li>
            </ul>
          </div>

          <div className="rounded-2xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900">
              One-tap irrigation logging
            </h3>
            <p className="mt-1 text-sm text-gray-600">
              Log by gallons or runtime + GPM. SMS reply support (“1” or “1
              5000”) feeds this same history.
            </p>
            <ul className="mt-3 divide-y divide-gray-100 text-sm">
              <li className="flex justify-between py-2">
                <span>Jun 12, 2026 · 23 hrs (1,380 min) @ 24 GPM</span>
                <span className="font-medium">33,120 gal</span>
              </li>
              <li className="flex justify-between py-2">
                <span>Jun 10, 2026 · Manual entry</span>
                <span className="font-medium">9,000 gal</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="space-y-4 lg:col-span-2">
          <h2 className="text-xl font-semibold text-gray-900">
            Savings and reporting
          </h2>
          <SavingsCard rows={demoSavingsRows} />
          <div className="rounded-2xl border border-gray-200 p-4">
            <WeeklySavingsChart rows={demoSavingsRows} />
          </div>

          <div className="rounded-2xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900">
              Scheduler pipeline
            </h3>
            <ol className="mt-3 space-y-2 text-sm text-gray-700">
              <li>
                02:00 — Pull ET (OpenET + CIMIS gap-fill) and run AquaCrop
              </li>
              <li>02:05 — Trigger SMS only on severity escalation</li>
              <li>03:00 — Compute weekly water, energy, and CO₂ savings</li>
              <li>04:00 — Refresh anonymized public impact aggregates</li>
            </ol>
          </div>
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900">
          What this proves
        </h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Capability
            title="Operational alerts"
            body="AquaCrop-driven decisions with clear as-of dates and days-to-stress."
          />
          <Capability
            title="Spatial explainability"
            body="NDVI overlay explains where stress appears without replacing trigger logic."
          />
          <Capability
            title="Farmer-friendly logging"
            body="UI + SMS inputs normalize irrigation entries into one history."
          />
          <Capability
            title="Grant-ready outcomes"
            body="Automatic gallons, kWh, and CO₂ metrics for reporting and impact dashboards."
          />
        </div>
      </section>
    </main>
  );
}

function Stat({
  title,
  value,
  accent = false,
}: {
  title: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-gray-200 p-5">
      <p className="text-sm text-gray-500">{title}</p>
      <p
        className={`mt-1 text-3xl font-bold ${accent ? "text-amber-600" : "text-gray-900"}`}
      >
        {value}
      </p>
    </div>
  );
}

function Capability({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-xl bg-gray-50 p-4">
      <h3 className="font-semibold text-gray-900">{title}</h3>
      <p className="mt-1 text-sm text-gray-600">{body}</p>
    </div>
  );
}
