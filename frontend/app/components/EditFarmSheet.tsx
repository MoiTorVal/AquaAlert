"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import dynamic from "next/dynamic";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { updateFarm, type Farm } from "../lib/api";
import {
  EditFarmFormSchema,
  SOIL_TEXTURES,
  type EditFarmFormValues,
} from "../lib/validators";

// Leaflet requires `window`; load client-side only (see FieldMapDraw.tsx).
const FieldMapDraw = dynamic(() => import("./FieldMapDraw"), {
  ssr: false,
  loading: () => <div className="h-80 animate-pulse rounded-xl bg-gray-100" />,
});

export default function EditFarmSheet({
  farm,
  onClose,
  onSaved,
}: {
  farm: Farm;
  onClose: () => void;
  onSaved: (farm: Farm) => void;
}) {
  const t = useTranslations("createFarm");
  const tSoil = useTranslations("soil");
  const [serverError, setServerError] = useState<string | null>(null);
  const [fieldPolygon, setFieldPolygon] = useState<string | null>(
    farm.field_polygon,
  );
  const [drawing, setDrawing] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EditFarmFormValues>({
    resolver: zodResolver(EditFarmFormSchema),
    defaultValues: {
      name: farm.name,
      location: farm.location ?? "",
      crop_type: farm.crop_type ?? "",
      planting_date: farm.planting_date ?? "",
      soil_type: farm.soil_type ?? "",
      acreage_acres: farm.acreage_acres?.toString() ?? "",
    },
    mode: "onBlur",
  });

  const onSubmit = async (values: EditFarmFormValues) => {
    setServerError(null);
    try {
      const saved = await updateFarm(farm.id, {
        name: values.name,
        location: values.location || null,
        crop_type: values.crop_type || null,
        planting_date: values.planting_date || null,
        soil_type: values.soil_type || null,
        acreage_acres: values.acreage_acres
          ? Number(values.acreage_acres)
          : null,
        field_polygon: fieldPolygon,
      });
      onSaved(saved);
      onClose();
    } catch (err) {
      setServerError(
        err instanceof Error ? err.message : "Failed to save farm",
      );
    }
  };

  const inputClass = "mt-1 w-full rounded-lg border border-gray-300 p-2";

  return (
    <div
      // z-[60] keeps the dialog above the fixed navbar (z-50)
      className="fixed inset-0 z-[60] flex items-end justify-center bg-black/40 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-label={`Edit ${farm.name}`}
    >
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-t-2xl bg-white p-6 sm:rounded-2xl">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Edit farm</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 flex flex-col gap-4">
          <label className="text-sm">
            <span className="text-gray-700">Name</span>
            <input {...register("name")} className={inputClass} />
            {errors.name && (
              <span className="text-xs text-red-600">{errors.name.message}</span>
            )}
          </label>
          <label className="text-sm">
            <span className="text-gray-700">Location</span>
            <input {...register("location")} className={inputClass} />
          </label>
          <label className="text-sm">
            <span className="text-gray-700">Crop</span>
            <input {...register("crop_type")} className={inputClass} />
          </label>
          <label className="text-sm">
            <span className="text-gray-700">Planting date</span>
            <input type="date" {...register("planting_date")} className={inputClass} />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-sm">
              <span className="text-gray-700">Soil type</span>
              <select {...register("soil_type")} className={inputClass}>
                <option value="">—</option>
                {SOIL_TEXTURES.map((s) => (
                  <option key={s} value={s}>
                    {tSoil(s)}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              <span className="text-gray-700">Acres</span>
              <input
                type="number"
                inputMode="decimal"
                step="any"
                {...register("acreage_acres")}
                className={inputClass}
              />
              {errors.acreage_acres && (
                <span className="text-xs text-red-600">
                  {errors.acreage_acres.message}
                </span>
              )}
            </label>
          </div>

          <div className="text-sm">
            <span className="text-gray-700">{t("fieldBoundary")}</span>
            <p className="mt-1 text-xs text-gray-500">{t("fieldBoundaryHint")}</p>
            <div className="mt-2">
              <FieldMapDraw
                onChange={setFieldPolygon}
                onDrawingChange={setDrawing}
                initialWkt={farm.field_polygon}
              />
            </div>
            <p
              role="status"
              className={`mt-1 text-xs ${
                drawing
                  ? "text-amber-600"
                  : fieldPolygon
                    ? "text-green-700"
                    : "text-gray-400"
              }`}
            >
              {drawing
                ? t("boundaryDrawing")
                : fieldPolygon
                  ? t("boundaryCaptured")
                  : t("boundaryPending")}
            </p>
          </div>

          {serverError && (
            <p role="alert" className="text-sm text-red-600">
              {serverError}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-lg bg-green-600 py-3 font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            {isSubmitting ? "Saving…" : "Save changes"}
          </button>
        </form>
      </div>
    </div>
  );
}
