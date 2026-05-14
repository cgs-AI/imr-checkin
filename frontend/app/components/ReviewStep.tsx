"use client";

import type { HostSummary } from "@/lib/api";
import type { VisitorDraft } from "@/checkin/page";

type Props = {
  visitor: VisitorDraft;
  host: HostSummary | null;
  error: string | null;
  onBack: () => void;
  onSubmit: () => void;
};

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="review-line">
      <span>{label}</span>
      <span>{value || "—"}</span>
    </div>
  );
}

export default function ReviewStep({ visitor, host, error, onBack, onSubmit }: Props) {
  return (
    <section className="card" aria-labelledby="review-heading">
      <h1 id="review-heading">Review your details</h1>
      <Row label="Name" value={visitor.full_name} />
      <Row label="Email" value={visitor.email} />
      <Row label="Phone" value={visitor.phone} />
      <Row label="Company" value={visitor.company} />
      <Row label="Job title" value={visitor.job_title} />
      <Row label="IMR host" value={host?.display_name ?? ""} />

      {error && <p className="error">{error}</p>}

      <button onClick={onSubmit}>Check in</button>
      <div className="row">
        <button className="secondary" onClick={onBack}>
          Edit
        </button>
      </div>
    </section>
  );
}
