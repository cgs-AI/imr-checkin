"use client";

import { useState } from "react";
import { api, type VisitorSummary } from "@/lib/api";

type Props = {
  onSkip: () => void;
  onMatch: (match: VisitorSummary | null) => void;
};

export default function LookupStep({ onSkip, onMatch }: Props) {
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [info, setInfo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleLookup = async () => {
    if (!email && !phone) {
      onSkip();
      return;
    }
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const result = await api.lookupVisitor({
        email: email.trim() || undefined,
        phone: phone.trim() || undefined,
      });
      if (result.match) {
        onMatch(result.match);
        return;
      }
      if (result.ambiguous) {
        setInfo("We found more than one record. Please continue and enter your details.");
      } else {
        setInfo("No existing record found. Please continue and enter your details.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lookup failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card" aria-labelledby="lookup-heading">
      <h1 id="lookup-heading">Are you a returning visitor?</h1>
      <p className="muted">
        Enter the email or phone number you used last time so we can pre-fill your details.
      </p>

      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        autoComplete="email"
        inputMode="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <label htmlFor="phone">Phone</label>
      <input
        id="phone"
        type="tel"
        autoComplete="tel"
        inputMode="tel"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
      />
      <p className="helper">You can type or use your phone keyboard microphone.</p>

      {info && <p className="muted">{info}</p>}
      {error && <p className="error">{error}</p>}

      <button onClick={handleLookup} disabled={busy}>
        {busy ? "Checking…" : "Continue"}
      </button>
      <div className="row">
        <button className="secondary" onClick={onSkip} disabled={busy}>
          I&apos;m a new visitor
        </button>
      </div>
    </section>
  );
}
