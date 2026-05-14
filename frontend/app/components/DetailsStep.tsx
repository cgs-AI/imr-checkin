"use client";

import type { VisitorDraft } from "@/checkin/page";

type Props = {
  visitor: VisitorDraft;
  setVisitor: (v: VisitorDraft) => void;
  onBack: () => void;
  onContinue: () => void;
};

export default function DetailsStep({ visitor, setVisitor, onBack, onContinue }: Props) {
  const update = (field: keyof VisitorDraft, value: string) =>
    setVisitor({ ...visitor, [field]: value });

  const canContinue = visitor.full_name.trim().length > 0;

  return (
    <section className="card" aria-labelledby="details-heading">
      <h1 id="details-heading">Your details</h1>
      <p className="helper">You can type or use your phone keyboard microphone.</p>

      <label htmlFor="full_name">Full name</label>
      <input
        id="full_name"
        type="text"
        autoComplete="name"
        value={visitor.full_name}
        onChange={(e) => update("full_name", e.target.value)}
      />

      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        autoComplete="email"
        inputMode="email"
        value={visitor.email}
        onChange={(e) => update("email", e.target.value)}
      />

      <label htmlFor="phone">Phone</label>
      <input
        id="phone"
        type="tel"
        autoComplete="tel"
        inputMode="tel"
        value={visitor.phone}
        onChange={(e) => update("phone", e.target.value)}
      />

      <label htmlFor="company">Company</label>
      <input
        id="company"
        type="text"
        autoComplete="organization"
        value={visitor.company}
        onChange={(e) => update("company", e.target.value)}
      />

      <label htmlFor="job_title">Job title</label>
      <input
        id="job_title"
        type="text"
        autoComplete="organization-title"
        value={visitor.job_title}
        onChange={(e) => update("job_title", e.target.value)}
      />

      <button onClick={onContinue} disabled={!canContinue}>
        Continue
      </button>
      <div className="row">
        <button className="secondary" onClick={onBack}>
          Back
        </button>
      </div>
    </section>
  );
}
