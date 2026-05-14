"use client";

import type { CheckinConfig } from "@/lib/api";

type Props = {
  config: CheckinConfig;
  onContinue: () => void;
};

export default function PrivacyStep({ config, onContinue }: Props) {
  return (
    <section className="card" aria-labelledby="privacy-heading">
      <h1 id="privacy-heading">Privacy notice</h1>
      <p style={{ whiteSpace: "pre-line" }}>{config.privacy_text}</p>
      <p className="muted">
        By tapping Continue, you confirm that you have read this notice.
      </p>
      <button onClick={onContinue}>Continue</button>
    </section>
  );
}
