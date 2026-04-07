"use client";

import { useEffect, useState } from "react";
import { getFarms, getWaterStress } from "../api/farms";
import { Farm, WaterStressResponse } from "../types/farm";

export default function Home() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [stressMap, setStressMap] = useState<
    Record<number, WaterStressResponse>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await getFarms(1); // hardcoded to fetch the first page of farms
        const farmList = res.data;
        setFarms(farmList);

        const entries = await Promise.all(
          farmList.map(async (farm) => {
            const stressRes = await getWaterStress(farm.id);
            return [farm.id, stressRes.data] as const;
          }),
        );

        const stressResults = Object.fromEntries(entries);
        setStressMap(stressResults);
      } catch (error) {
        console.error("Error fetching farms:", error);
        setError("Failed to fetch farms. Please try again later.");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) return <p className="p-8 text-zinc-500">Loading...</p>;
  if (error) return <p className="p-8 text-red-500">{error}</p>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Farm Dashboard</h1>

      {farms.length === 0 && <p className="text-zinc-500">No farms found.</p>}

      <div className="grid gap-4">
        {farms.map((farm) => {
          const stress = stressMap[farm.id];
          return (
            <div
              key={farm.id}
              className="border rounded-lg p-4 flex justify-between items-center"
            >
              <div>
                <h2 className="text-lg font-semibold">{farm.name}</h2>
                <p className="text-sm text-zinc-500">
                  {farm.crop_type} · {farm.location}
                </p>
              </div>

              {stress && (
                <div className="text-right">
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                      stress.severity === "critical"
                        ? "bg-red-100 text-red-700"
                        : stress.severity === "moderate"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-green-100 text-green-700"
                    }`}
                  >
                    {stress.severity ?? "ok"}
                  </span>
                  {stress.stress_in_days !== null && (
                    <p className="text-xs text-zinc-500 mt-1">
                      Stress in {stress.stress_in_days} days
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
