"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { deleteFarm, getFarms, type Farm } from "../lib/api";
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

function FarmsContent() {
  const router = useRouter();
  const [farms, setFarms] = useState<Farm[]>([]);
  const [creating, setCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Farm | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    getFarms()
      .then(setFarms)
      .catch(() => {
        setError("Failed to load farms. Please try again later.");
      })
      .finally(() => setLoading(false));
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

  return (
    // pt-28 clears the fixed navbar (matches /impact)
    <main className="p-6 pt-28 max-w-5xl mx-auto">
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
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="px-3 pb-3 font-medium">Name</th>
              <th className="px-3 pb-3 font-medium">Crop</th>
              <th className="px-3 pb-3 font-medium">Location</th>
              <th className="px-3 pb-3 font-medium">Acres</th>
              <th className="px-3 pb-3 font-medium">Planted</th>
              <th className="px-3 pb-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {farms.map((farm) => (
              <tr key={farm.id} className="border-b hover:bg-gray-50">
                <td className="px-3 py-3">
                  <Link
                    href={`/farms/${farm.id}`}
                    className="font-medium text-green-700 hover:underline"
                  >
                    {farm.name}
                  </Link>
                </td>
                <td className="px-3 py-3 text-gray-600">{farm.crop_type ?? "—"}</td>
                <td className="px-3 py-3 text-gray-600">{farm.location ?? "—"}</td>
                <td className="px-3 py-3 text-gray-600">
                  {farm.acreage_acres ?? "—"}
                </td>
                <td className="px-3 py-3 text-gray-600">
                  {farm.planting_date ?? "—"}
                </td>
                <td className="px-3 py-3 flex gap-2">
                  <button
                    onClick={() => setEditing(farm)}
                    className="text-gray-500 hover:text-gray-800 text-xs border rounded px-2 py-1"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(farm)}
                    className="text-red-500 hover:text-red-700 text-xs border border-red-200 rounded px-2 py-1"
                  >
                    Delete
                  </button>
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
            className="block border rounded-xl p-4 hover:bg-gray-50"
          >
            <div className="font-semibold text-green-700">{farm.name}</div>
            <div className="text-sm text-gray-500 mt-1">
              {farm.crop_type ?? "No crop"} · {farm.location ?? "No location"}
            </div>
            <div className="text-sm text-gray-400 mt-1">
              {farm.acreage_acres ? `${farm.acreage_acres} ac` : "Area unknown"}{" "}
              · Planted {farm.planting_date ?? "unknown"}
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

function FarmsSkeleton() {
  return (
    <main className="p-6 pt-28 max-w-5xl mx-auto">
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
    <main className="p-6 max-w-5xl mx-auto flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="text-5xl mb-4">⚠️</div>
      <h2 className="text-xl font-semibold mb-2">Failed to load farms</h2>
      <p className="text-red-500 text-sm">{message}</p>
    </main>
  );
}
