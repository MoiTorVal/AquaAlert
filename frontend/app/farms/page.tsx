"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLocale } from "next-intl";
import {
  deleteFarm,
  getFarms,
  getWaterStress,
  type Farm,
  type WaterStress,
} from "../lib/api";
import { displayName, formatDate } from "../lib/format";
import EditFarmSheet from "../components/EditFarmSheet";
import CreateFarmSheet from "../components/CreateFarmSheet";
import ProtectedRoute from "../components/ProtectedRoute";

export default function FarmsPage() {
  return (
    <ProtectedRoute>
      <FarmsContent />
    </ProtectedRoute>
  );
}

// null = no assessment yet; absent key = still loading
type StressMap = Record<number, WaterStress | null>;

function FarmsContent() {
  const router = useRouter();
  const locale = useLocale();
  const [farms, setFarms] = useState<Farm[]>([]);
  const [stressMap, setStressMap] = useState<StressMap>({});
  const [creating, setCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Farm | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getFarms()
      .then((loaded) => {
        if (!active) return;
        setFarms(loaded);
        setLoading(false);
        // Stress loads per farm after the list renders; a farm whose
        // stress call fails just keeps showing the loading dash.
        loaded.forEach((farm) => {
          getWaterStress(farm.id)
            .then((stress) => {
              if (active)
                setStressMap((prev) => ({ ...prev, [farm.id]: stress }));
            })
            .catch(() => {});
        });
      })
      .catch(() => {
        if (!active) return;
        setError("Failed to load farms. Please try again later.");
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const handleDelete = async (farm: Farm) => {
    if (!window.confirm(`Delete "${farm.name}"? This cannot be undone.`)) {
      return;
    }
    setActionError(null);
    try {
      await deleteFarm(farm.id);
      setFarms((prev) => prev.filter((f) => f.id !== farm.id));
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Failed to delete farm",
      );
    }
  };

  if (loading) return <FarmsSkeleton />;
  if (error) return <ErrorState message={error} />;
  if (farms.length === 0)
    return (
      <>
        <EmptyState onCreate={() => setCreating(true)} />
        <CreateFarmSheet
          open={creating}
          onClose={() => setCreating(false)}
          onCreated={(farm) => router.push(`/farms/${farm.id}`)}
        />
      </>
    );

  const totalAcres = farms.reduce((sum, f) => sum + (f.acreage_acres ?? 0), 0);
  const needsAttention = farms.filter((f) => {
    const severity = stressMap[f.id]?.severity;
    return severity === "yellow" || severity === "red";
  }).length;
  const stressLoaded = farms.every((f) => f.id in stressMap);

  return (
    // pt-28 clears the fixed navbar (matches /impact)
    <main className="p-6 pt-28 max-w-6xl mx-auto">
      {actionError && (
        <p role="alert" className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {actionError}
        </p>
      )}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">My Farms</h1>
        <button
          onClick={() => setCreating(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700"
        >
          + Add Farm
        </button>
      </div>

      <div className="mb-6 grid grid-cols-3 gap-4">
        <SummaryStat label="Farms" value={String(farms.length)} />
        <SummaryStat
          label="Total acres"
          value={totalAcres > 0 ? totalAcres.toLocaleString() : "—"}
        />
        <SummaryStat
          label="Need attention"
          value={stressLoaded ? String(needsAttention) : "…"}
          accent={needsAttention > 0}
        />
      </div>

      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-gray-200 text-left text-gray-500">
              <th className="px-3 pb-3 font-medium">Name</th>
              <th className="px-3 pb-3 font-medium">Status</th>
              <th className="px-3 pb-3 font-medium">Crop</th>
              <th className="px-3 pb-3 font-medium">Location</th>
              <th className="px-3 pb-3 font-medium text-right">Acres</th>
              <th className="px-3 pb-3 font-medium">Planted</th>
              <th className="px-3 pb-3" aria-label="Actions" />
            </tr>
          </thead>
          <tbody>
            {farms.map((farm) => (
              <tr
                key={farm.id}
                onClick={() => router.push(`/farms/${farm.id}`)}
                className="cursor-pointer border-b border-gray-200 hover:bg-gray-50"
              >
                <td className="px-3 py-3 font-medium text-gray-900">
                  {displayName(farm.name)}
                </td>
                <td className="px-3 py-3">
                  <StatusCell
                    stress={stressMap[farm.id]}
                    loaded={farm.id in stressMap}
                  />
                </td>
                <td className="px-3 py-3 text-gray-600">
                  {farm.crop_type ? displayName(farm.crop_type) : "—"}
                </td>
                <td className="px-3 py-3 text-gray-600">
                  {farm.location ? displayName(farm.location) : "—"}
                </td>
                <td className="px-3 py-3 text-right tabular-nums text-gray-600">
                  {farm.acreage_acres?.toLocaleString() ?? "—"}
                </td>
                <td className="px-3 py-3 text-gray-600">
                  {formatDate(farm.planting_date, locale)}
                </td>
                <td className="px-3 py-3 text-right">
                  <RowMenu
                    farmName={farm.name}
                    onEdit={() => setEditing(farm)}
                    onDelete={() => handleDelete(farm)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="sm:hidden flex flex-col gap-4">
        {farms.map((farm) => (
          <Link
            key={farm.id}
            href={`/farms/${farm.id}`}
            className="block border border-gray-200 rounded-xl p-4 hover:bg-gray-50"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-900">
                {displayName(farm.name)}
              </span>
              <StatusCell
                stress={stressMap[farm.id]}
                loaded={farm.id in stressMap}
              />
            </div>
            <div className="text-sm text-gray-500 mt-1">
              {farm.crop_type ? displayName(farm.crop_type) : "No crop"} ·{" "}
              {farm.location ? displayName(farm.location) : "No location"}
            </div>
            <div className="text-sm text-gray-400 mt-1">
              {farm.acreage_acres ? `${farm.acreage_acres} ac` : "Area unknown"}{" "}
              · Planted {formatDate(farm.planting_date, locale)}
            </div>
          </Link>
        ))}
      </div>

      <CreateFarmSheet
        open={creating}
        onClose={() => setCreating(false)}
        onCreated={(farm) => router.push(`/farms/${farm.id}`)}
      />
      {editing && (
        <EditFarmSheet
          farm={editing}
          onClose={() => setEditing(null)}
          onSaved={(saved) =>
            setFarms((prev) => prev.map((f) => (f.id === saved.id ? saved : f)))
          }
        />
      )}
    </main>
  );
}

function SummaryStat({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-xl border border-gray-200 p-4">
      <div className="text-sm text-gray-500">{label}</div>
      <div
        className={`mt-1 text-2xl font-bold tabular-nums ${
          accent ? "text-red-600" : "text-gray-900"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

const STATUS_STYLES = {
  green: { dot: "bg-green-500", label: "Healthy" },
  yellow: { dot: "bg-yellow-400", label: "Approaching" },
  red: { dot: "bg-red-500", label: "Stressed" },
} as const;

function StatusCell({
  stress,
  loaded,
}: {
  stress: WaterStress | null | undefined;
  loaded: boolean;
}) {
  if (!loaded) {
    return (
      <span className="inline-block h-2.5 w-16 animate-pulse rounded bg-gray-100" />
    );
  }
  const severity = stress?.severity;
  if (!severity) {
    return (
      <span className="inline-flex items-center gap-2 text-gray-400">
        <span aria-hidden className="h-2.5 w-2.5 rounded-full bg-gray-300" />
        Pending
      </span>
    );
  }
  const { dot, label } = STATUS_STYLES[severity];
  const days = stress?.days_to_stress;
  return (
    <span className="inline-flex items-center gap-2 text-gray-700">
      <span aria-hidden className={`h-2.5 w-2.5 rounded-full ${dot}`} />
      {label}
      {severity !== "red" && days != null && (
        <span className="text-xs text-gray-400">{days}d to stress</span>
      )}
    </span>
  );
}

/** Three-dot menu so Edit/Delete don't shout from every row. Clicks must not
 * bubble to the row, which navigates. */
function RowMenu({
  farmName,
  onEdit,
  onDelete,
}: {
  farmName: string;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <div ref={ref} className="relative inline-block" onClick={(e) => e.stopPropagation()}>
      <button
        aria-label={`Actions for ${farmName}`}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
      >
        <span aria-hidden className="text-lg leading-none">⋯</span>
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 z-10 mt-1 w-28 rounded-lg border border-gray-200 bg-white py-1 text-left shadow-lg"
        >
          <button
            role="menuitem"
            onClick={() => {
              setOpen(false);
              onEdit();
            }}
            className="block w-full px-3 py-1.5 text-left text-gray-700 hover:bg-gray-50"
          >
            Edit
          </button>
          <button
            role="menuitem"
            onClick={() => {
              setOpen(false);
              onDelete();
            }}
            className="block w-full px-3 py-1.5 text-left text-red-600 hover:bg-red-50"
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
}

function FarmsSkeleton() {
  return (
    <main className="p-6 pt-28 max-w-6xl mx-auto">
      <div className="h-8 w-32 bg-gray-200 rounded animate-pulse mb-6" />
      <div className="flex flex-col gap-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
        ))}
      </div>
    </main>
  );
}

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center text-center p-6">
      <h2 className="text-xl font-semibold mb-2">No farms yet</h2>
      <p className="text-gray-400 mb-6">
        Add your first farm to start tracking water stress.
      </p>
      <button
        onClick={onCreate}
        className="bg-gray-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-700"
      >
        + Create your first farm
      </button>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <main className="p-6 max-w-6xl mx-auto flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="text-5xl mb-4">⚠️</div>
      <h2 className="text-xl font-semibold mb-2">Failed to load farms</h2>
      <p className="text-red-500 text-sm">{message}</p>
    </main>
  );
}
