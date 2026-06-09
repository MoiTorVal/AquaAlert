"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { logIrrigationEvent } from "../lib/api";
import {
  IrrigationLogFormSchema,
  gallonsFromForm,
  type IrrigationLogFormValues,
} from "../lib/validators";

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function IrrigationLogSheet({
  farmId,
  open,
  onClose,
  onLogged,
}: {
  farmId: number;
  open: boolean;
  onClose: () => void;
  onLogged: () => void;
}) {
  const t = useTranslations("irrigationLog");
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<IrrigationLogFormValues>({
    resolver: zodResolver(IrrigationLogFormSchema),
    defaultValues: { event_date: todayISO(), mode: "gallons" },
    mode: "onBlur",
  });
  const mode = watch("mode");

  if (!open) return null;

  const onSubmit = async (values: IrrigationLogFormValues) => {
    setServerError(null);
    try {
      await logIrrigationEvent(farmId, {
        event_date: values.event_date,
        gallons_applied: gallonsFromForm(values),
      });
      reset({ event_date: todayISO(), mode: values.mode });
      onLogged();
      onClose();
    } catch (err) {
      setServerError(
        err instanceof Error ? err.message : t("failed"),
      );
    }
  };

  return (
    <div
      className="fixed inset-0 z-20 flex items-end justify-center bg-black/40 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-label={t("title")}
    >
      <div className="w-full max-w-md rounded-t-2xl bg-white p-6 sm:rounded-2xl">
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

        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 flex flex-col gap-4">
          <label className="text-sm">
            <span className="text-gray-700">{t("date")}</span>
            <input
              type="date"
              {...register("event_date")}
              className="mt-1 w-full rounded-lg border border-gray-300 p-2"
            />
            {errors.event_date && (
              <span className="text-xs text-red-600">{errors.event_date.message}</span>
            )}
          </label>

          <fieldset className="flex gap-4 text-sm">
            <legend className="sr-only">{t("modeQuestion")}</legend>
            <label className="flex items-center gap-1">
              <input type="radio" value="gallons" {...register("mode")} />
              {t("gallons")}
            </label>
            <label className="flex items-center gap-1">
              <input type="radio" value="runtime" {...register("mode")} />
              {t("runtime")}
            </label>
          </fieldset>

          {mode === "gallons" ? (
            <label className="text-sm">
              <span className="text-gray-700">{t("gallonsApplied")}</span>
              <input
                type="number"
                inputMode="decimal"
                step="any"
                {...register("gallons")}
                className="mt-1 w-full rounded-lg border border-gray-300 p-2"
              />
              {errors.gallons && (
                <span className="text-xs text-red-600">{errors.gallons.message}</span>
              )}
            </label>
          ) : (
            <div className="flex gap-3">
              <label className="flex-1 text-sm">
                <span className="text-gray-700">{t("hoursRun")}</span>
                <input
                  type="number"
                  inputMode="decimal"
                  step="any"
                  {...register("hours")}
                  className="mt-1 w-full rounded-lg border border-gray-300 p-2"
                />
                {errors.hours && (
                  <span className="text-xs text-red-600">{errors.hours.message}</span>
                )}
              </label>
              <label className="flex-1 text-sm">
                <span className="text-gray-700">{t("pumpFlow")}</span>
                <input
                  type="number"
                  inputMode="decimal"
                  step="any"
                  {...register("gpm")}
                  className="mt-1 w-full rounded-lg border border-gray-300 p-2"
                />
                {errors.gpm && (
                  <span className="text-xs text-red-600">{errors.gpm.message}</span>
                )}
              </label>
            </div>
          )}

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
            {isSubmitting ? t("saving") : t("save")}
          </button>
        </form>
      </div>
    </div>
  );
}
