import { render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import en from "../messages/en.json";

export function renderWithIntl(ui: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="en" messages={en} timeZone="America/Los_Angeles">
      {ui}
    </NextIntlClientProvider>,
  );
}
