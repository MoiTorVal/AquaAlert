"use client";

import { useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { updateMe, type Alert, type StressSeverity } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { formatDate } from "../lib/format";

const SEVERITY_DOT: Record<StressSeverity, string> = {
  green: "bg-green-500",
  yellow: "bg-yellow-400",
  red: "bg-red-500",
};

/** Alert history for one farm plus the account-wide SMS opt-in. The toggle
 * lives here (not a settings page) because alerts are the thing being
 * toggled — a farmer should find both in one place. */
export default function AlertsCard({ alerts }: { alerts: Alert[] }) {
  const t = useTranslations("alerts");
  const locale = useLocale();
  const { user, setUser } = useAuth();
  const [phone, setPhone] = useState("");
  const [needsPhone, setNeedsPhone] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const smsEnabled = user?.sms_alerts_enabled ?? false;

  const toggleSms = async () => {
    if (!user || saving) return;
    setError(null);
    if (!smsEnabled && user.phone_number == null && !needsPhone) {
      // Backend rejects enabling SMS without a phone number — ask first.
      setNeedsPhone(true);
      return;
    }
    setSaving(true);
    try {
      const body = smsEnabled
        ? { sms_alerts_enabled: false }
        : {
            sms_alerts_enabled: true,
            ...(user.phone_number == null ? { phone_number: phone } : {}),
          };
      setUser(await updateMe(body));
      setNeedsPhone(false);
      setPhone("");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("saveFailed"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <section
      data-testid="alerts-card"
      className="rounded-2xl border border-gray-200 p-6"
    >
      <h2 className="text-lg font-semibold">{t("title")}</h2>

      <div className="mt-3 flex items-center justify-between gap-4">
        <div className="text-sm">
          <p className="font-medium text-gray-800">{t("smsLabel")}</p>
          <p className="mt-0.5 text-gray-500">
            {smsEnabled && user?.phone_number
              ? t("smsOnTo", { phone: user.phone_number })
              : t("smsOff")}
          </p>
        </div>
        <button
          role="switch"
          aria-checked={smsEnabled}
          aria-label={t("smsLabel")}
          onClick={toggleSms}
          disabled={saving}
          className={`relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-50 ${
            smsEnabled ? "bg-green-600" : "bg-gray-300"
          }`}
        >
          <span
            aria-hidden
            className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
              smsEnabled ? "left-[22px]" : "left-0.5"
            }`}
          />
        </button>
      </div>

      {needsPhone && !smsEnabled && (
        <div className="mt-3 rounded-lg bg-gray-50 p-3">
          <label className="block text-sm">
            <span className="text-gray-700">{t("phoneLabel")}</span>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+15551234567"
              className="mt-1 w-full rounded-lg border border-gray-300 p-2"
            />
          </label>
          <button
            onClick={toggleSms}
            disabled={saving || phone.trim() === ""}
            className="mt-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            {t("enableSms")}
          </button>
        </div>
      )}
      {error && (
        <p role="alert" className="mt-2 text-sm text-red-600">
          {error}
        </p>
      )}

      <h3 className="mt-5 text-sm font-medium text-gray-700">{t("history")}</h3>
      {alerts.length === 0 ? (
        <p className="mt-2 text-sm text-gray-500">{t("empty")}</p>
      ) : (
        <ul className="mt-2 divide-y divide-gray-100 text-sm">
          {alerts.map((alert) => (
            <li key={alert.id} className="flex items-center justify-between py-2">
              <span className="flex items-center gap-2">
                <span
                  aria-hidden
                  className={`h-2.5 w-2.5 rounded-full ${SEVERITY_DOT[alert.severity]}`}
                />
                <span className="text-gray-700">
                  {alert.severity === "red"
                    ? t("redAlert")
                    : alert.days_to_stress != null
                      ? t("yellowAlertDays", { days: alert.days_to_stress })
                      : t("yellowAlert")}
                </span>
              </span>
              <span className="flex items-center gap-2">
                {alert.feedback != null && (
                  <span
                    className={`rounded px-2 py-0.5 text-xs ${
                      alert.feedback === "yes"
                        ? "bg-red-50 text-red-700"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {alert.feedback === "yes"
                      ? t("feedbackYes")
                      : t("feedbackNo")}
                  </span>
                )}
                <span className="text-gray-500">
                  {formatDate(alert.as_of_date, locale)}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
