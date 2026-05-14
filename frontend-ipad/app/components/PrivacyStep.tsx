"use client";

import type { CheckinConfig } from "@/lib/api";

type Props = {
  config: CheckinConfig;
  onContinue: () => void;
};

const KIOSK_PRIVACY_BODY = `IMR will collect the details you submit in this form to manage your visit, notify your IMR host, and keep a record of your visit.

You may use the iPad's built-in dictation feature to fill in the form. IMR does not receive or store audio. IMR only receives the text you submit.

Your visit details may be stored in IMR systems, including HubSpot and Microsoft 365, for visitor management and relationship history.

By continuing, you confirm that the information you provide is accurate and that you understand how it will be used.`;

export default function PrivacyStep({ config: _config, onContinue }: Props) {
  return (
    <section className="card" aria-labelledby="privacy-heading">
      <h1 id="privacy-heading">Privacy notice</h1>
      <p style={{ whiteSpace: "pre-line" }}>{KIOSK_PRIVACY_BODY}</p>
      <button className="primary-action" onClick={onContinue}>
        Continue
      </button>
    </section>
  );
}
