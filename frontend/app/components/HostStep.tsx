"use client";

import { useEffect, useState } from "react";
import { api, type HostSummary } from "@/lib/api";

type Props = {
  host: HostSummary | null;
  setHost: (h: HostSummary | null) => void;
  minChars: number;
  onBack: () => void;
  onContinue: () => void;
};

export default function HostStep({ host, setHost, minChars, onBack, onContinue }: Props) {
  const [query, setQuery] = useState(host?.display_name ?? "");
  const [results, setResults] = useState<HostSummary[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < minChars) {
      setResults([]);
      return;
    }
    const handle = setTimeout(async () => {
      setBusy(true);
      setError(null);
      try {
        const hosts = await api.searchHosts(trimmed);
        setResults(hosts);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Search failed");
      } finally {
        setBusy(false);
      }
    }, 200);
    return () => clearTimeout(handle);
  }, [query, minChars]);

  return (
    <section className="card" aria-labelledby="host-heading">
      <h1 id="host-heading">Who are you visiting today?</h1>
      <label htmlFor="host-search">Search by name</label>
      <input
        id="host-search"
        type="search"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setHost(null);
        }}
        placeholder="Start typing a name"
      />
      <p className="helper">Type at least {minChars} characters to search.</p>

      {busy && <p className="muted">Searching…</p>}
      {error && <p className="error">{error}</p>}

      <div role="listbox" aria-label="Host suggestions">
        {results.map((option) => {
          const selected = host?.id === option.id;
          return (
            <button
              key={option.id}
              role="option"
              aria-selected={selected}
              className={`host-option${selected ? " selected" : ""}`}
              onClick={() => {
                setHost(option);
                setQuery(option.display_name);
                setResults([]);
              }}
            >
              <div style={{ fontWeight: 600 }}>{option.display_name}</div>
              {option.department && (
                <div className="muted">{option.department}</div>
              )}
            </button>
          );
        })}
      </div>

      <button onClick={onContinue} disabled={!host}>
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
