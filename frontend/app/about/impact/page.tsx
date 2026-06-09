import type { Metadata } from "next";
import Link from "next/link";
import { getTranslations } from "next-intl/server";

export const metadata: Metadata = {
  title: "Impact & Press — AquaAlert",
  description:
    "Water savings impact data, program background, and press resources for AquaAlert's small-farm water stress alerts.",
};

/** Press kit — static server component linking the live public dashboard. */
export default async function PressImpactPage() {
  const t = await getTranslations("press");

  return (
    <main className="mx-auto max-w-3xl p-6 pt-28">
      <h1 className="text-3xl font-bold">{t("title")}</h1>
      <p className="mt-3 text-gray-600">{t("intro")}</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">{t("whatTitle")}</h2>
        <p className="mt-2 text-gray-600">{t("whatBody")}</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">{t("dataTitle")}</h2>
        <p className="mt-2 text-gray-600">{t("dataBody")}</p>
        <Link
          href="/impact"
          className="mt-3 inline-block rounded-lg bg-green-600 px-5 py-2.5 font-medium text-white hover:bg-green-700"
        >
          {t("dashboardCta")}
        </Link>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">{t("methodTitle")}</h2>
        <ul className="mt-2 list-disc pl-5 text-gray-600">
          <li>{t("methodEt")}</li>
          <li>{t("methodSim")}</li>
          <li>{t("methodSavings")}</li>
          <li>{t("methodPrivacy")}</li>
        </ul>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">{t("contactTitle")}</h2>
        <p className="mt-2 text-gray-600">{t("contactBody")}</p>
      </section>
    </main>
  );
}
