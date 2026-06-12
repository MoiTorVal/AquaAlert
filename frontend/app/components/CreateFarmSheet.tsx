"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import dynamic from "next/dynamic";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { createFarm, type Farm } from "../lib/api";
import {
  CreateFarmFormSchema,
  SOIL_TEXTURES,
  type CreateFarmFormValues,
} from "../lib/validators";

// Leaflet requires `window`; load client-side only (see FieldMapDraw.tsx).
const FieldMapDraw = dynamic(() => import("./FieldMapDraw"), {
  ssr: false,
  loading: () => <div className="h-80 animate-pulse rounded-xl bg-gray-100" />,
});

export default function CreateFarmSheet({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (farm: Farm) => void;
}) {
  const t = useTranslations("createFarm");
  const tSoil = useTranslations("soil");
  const [serverError, setServerError] = useState<string | null>(null);
  const [fieldPolygon, setFieldPolygon] = useState<string | null>(null);
  const [drawing, setDrawing] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateFarmFormValues>({
    resolver: zodResolver(CreateFarmFormSchema),
    mode: "onBlur",
  });

  if (!open) return null;

  const onSubmit = async (values: CreateFarmFormValues) => {
    setServerError(null);
    try {
      const farm = await createFarm({
        name: values.name,
        location: values.location || null,
        crop_type: values.crop_type || null,
        planting_date: values.planting_date || null,
        soil_type: values.soil_type || null,
        acreage_acres: values.acreage_acres ? Number(values.acreage_acres) : null,
        field_polygon: fieldPolygon,
      });
      reset();
      setFieldPolygon(null);
      onCreated(farm);
    } catch (err) {
      setServerError(err instanceof Error ? err.message : t("failed"));
    }
  };

  const inputClass = "mt-1 w-full rounded-lg border border-gray-300 p-2";

  return (
    <div
      // z-[60] keeps the dialog above the fixed navbar (z-50)
      className="fixed inset-0 z-[60] flex items-end justify-center bg-black/40 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-label={t("title")}
    >
      {/* Sticky header + footer: the form scrolls, but the title/close and the
          submit button stay reachable however long the field list grows. */}
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-t-2xl bg-white sm:rounded-2xl">
        <div className="border-b border-gray-100 px-6 pb-4 pt-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">{t("title")}</h2>
            <button
              type="button"
              onClick={onClose}
              aria-label={t("close")}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <p className="mt-1 text-sm text-gray-500">{t("subtitle")}</p>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="flex flex-col gap-4 overflow-y-auto px-6 pt-4 text-sm"
        >
          <label>
            <span className="text-gray-700">{t("name")}</span>
            <input {...register("name")} className={inputClass} />
            {errors.name && (
              <span className="text-xs text-red-600">{errors.name.message}</span>
            )}
          </label>
          <label>
            <span className="text-gray-700">{t("location")}</span>
            <input {...register("location")} className={inputClass} />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label>
              <span className="text-gray-700">{t("crop")}</span>
              <input {...register("crop_type")} className={inputClass} />
            </label>
            <label>
              <span className="text-gray-700">{t("plantingDate")}</span>
              <input type="date" {...register("planting_date")} className={inputClass} />
            </label>
            <label>
              <span className="text-gray-700">{t("soil")}</span>
              <select {...register("soil_type")} className={inputClass}>
                <option value="">—</option>
                {SOIL_TEXTURES.map((s) => (
                  <option key={s} value={s}>
                    {tSoil(s)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span className="text-gray-700">{t("acreage")}</span>
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

          <div>
            <span className="text-gray-700">{t("fieldBoundary")}</span>
            <p className="mt-1 text-xs text-gray-500">{t("fieldBoundaryHint")}</p>
            <div className="mt-2">
              <FieldMapDraw
                onChange={setFieldPolygon}
                onDrawingChange={setDrawing}
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
            <p role="alert" className="text-red-600">
              {serverError}
            </p>
          )}

          <div className="sticky bottom-0 -mx-6 mt-2 border-t border-gray-100 bg-white px-6 py-4">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-lg bg-green-600 py-3 font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              {isSubmitting ? t("saving") : t("save")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
