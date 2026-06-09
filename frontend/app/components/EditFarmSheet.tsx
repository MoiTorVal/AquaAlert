"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { updateFarm, type Farm } from "../lib/api";
import {
  EditFarmFormSchema,
  type EditFarmFormValues,
} from "../lib/validators";

export default function EditFarmSheet({
  farm,
  onClose,
  onSaved,
}: {
  farm: Farm;
  onClose: () => void;
  onSaved: (farm: Farm) => void;
}) {
  const [serverError, setServerError] = useState<string | null>(null);
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
      });
      onSaved(saved);
      onClose();
    } catch (err) {
      setServerError(
        err instanceof Error ? err.message : "Failed to save farm",
      );
    }
  };

  return (
    <div
      className="fixed inset-0 z-20 flex items-end justify-center bg-black/40 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-label={`Edit ${farm.name}`}
    >
      <div className="w-full max-w-md rounded-t-2xl bg-white p-6 sm:rounded-2xl">
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
            <input
              {...register("name")}
              className="mt-1 w-full rounded-lg border border-gray-300 p-2"
            />
            {errors.name && (
              <span className="text-xs text-red-600">{errors.name.message}</span>
            )}
          </label>
          <label className="text-sm">
            <span className="text-gray-700">Location</span>
            <input
              {...register("location")}
              className="mt-1 w-full rounded-lg border border-gray-300 p-2"
            />
          </label>
          <label className="text-sm">
            <span className="text-gray-700">Crop</span>
            <input
              {...register("crop_type")}
              className="mt-1 w-full rounded-lg border border-gray-300 p-2"
            />
          </label>
          <label className="text-sm">
            <span className="text-gray-700">Planting date</span>
            <input
              type="date"
              {...register("planting_date")}
              className="mt-1 w-full rounded-lg border border-gray-300 p-2"
            />
          </label>

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
