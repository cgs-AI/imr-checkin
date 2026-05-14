"use client";

import { useEffect, useState } from "react";
import {
  api,
  type CheckinConfig,
  type CreateVisitRequest,
  type HostSummary,
  type VisitorSummary,
} from "@/lib/api";
import PrivacyStep from "@/components/PrivacyStep";
import LookupStep from "@/components/LookupStep";
import DetailsStep from "@/components/DetailsStep";
import HostStep from "@/components/HostStep";
import ReviewStep from "@/components/ReviewStep";
import ConfirmationStep from "@/components/ConfirmationStep";
import InactivityGuard from "@/components/InactivityGuard";

type Step =
  | "loading"
  | "privacy"
  | "lookup"
  | "details"
  | "host"
  | "review"
  | "submitting"
  | "confirmation"
  | "error";

export type VisitorDraft = {
  full_name: string;
  email: string;
  phone: string;
  company: string;
  job_title: string;
};

const emptyVisitor: VisitorDraft = {
  full_name: "",
  email: "",
  phone: "",
  company: "",
  job_title: "",
};

export default function CheckinPage() {
  const [step, setStep] = useState<Step>("loading");
  const [config, setConfig] = useState<CheckinConfig | null>(null);
  const [visitor, setVisitor] = useState<VisitorDraft>(emptyVisitor);
  const [existingVisitorId, setExistingVisitorId] = useState<string | null>(null);
  const [host, setHost] = useState<HostSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmationMessage, setConfirmationMessage] = useState<string>("");

  useEffect(() => {
    api
      .getConfig()
      .then((c) => {
        setConfig(c);
        setStep("privacy");
      })
      .catch((e) => {
        setError(e.message);
        setStep("error");
      });
  }, []);

  const applyMatch = (match: VisitorSummary | null) => {
    if (match) {
      setExistingVisitorId(match.id);
      setVisitor({
        full_name: match.full_name ?? "",
        email: match.email ?? "",
        phone: match.phone ?? "",
        company: match.company ?? "",
        job_title: match.job_title ?? "",
      });
    }
    setStep("details");
  };

  const resetState = () => {
    setVisitor(emptyVisitor);
    setExistingVisitorId(null);
    setHost(null);
    setError(null);
    setStep("privacy");
  };

  const submit = async () => {
    if (!config) return;
    setStep("submitting");
    setError(null);
    try {
      const payload: CreateVisitRequest = {
        visitor: {
          full_name: visitor.full_name.trim(),
          email: visitor.email.trim() || null,
          phone: visitor.phone.trim() || null,
          company: visitor.company.trim() || null,
          job_title: visitor.job_title.trim() || null,
        },
        host_id: host?.id ?? null,
        host_name_raw: host ? null : null,
        consent: {
          granted: true,
          consent_text_version: config.consent_text_version,
          consent_type: "visitor_checkin",
        },
        existing_visitor_id: existingVisitorId,
        source: "ipad_kiosk",
      };
      const response = await api.submitVisit(payload);
      setConfirmationMessage(response.confirmation_message);
      setStep("confirmation");
      setVisitor(emptyVisitor);
      setHost(null);
      setExistingVisitorId(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Submission failed");
      setStep("review");
    }
  };

  if (step === "loading") {
    return (
      <section className="card">
        <p>Loading…</p>
      </section>
    );
  }

  if (step === "error") {
    return (
      <section className="card">
        <h1>Something went wrong</h1>
        <p className="error">{error}</p>
        <button onClick={() => location.reload()}>Try again</button>
      </section>
    );
  }

  const isFlowActive =
    step === "privacy" ||
    step === "lookup" ||
    step === "details" ||
    step === "host" ||
    step === "review";

  return (
    <>
      {isFlowActive && (
        <InactivityGuard
          warningAfterMs={90_000}
          resetAfterMs={120_000}
          onReset={resetState}
        />
      )}
      {step === "privacy" && config && (
        <PrivacyStep config={config} onContinue={() => setStep("lookup")} />
      )}
      {step === "lookup" && (
        <LookupStep
          onSkip={() => setStep("details")}
          onMatch={applyMatch}
        />
      )}
      {step === "details" && (
        <DetailsStep
          visitor={visitor}
          setVisitor={setVisitor}
          onBack={() => setStep("lookup")}
          onContinue={() => setStep("host")}
        />
      )}
      {step === "host" && config && (
        <HostStep
          host={host}
          setHost={setHost}
          minChars={config.host_search_min_chars}
          onBack={() => setStep("details")}
          onContinue={() => setStep("review")}
        />
      )}
      {step === "review" && (
        <ReviewStep
          visitor={visitor}
          host={host}
          error={error}
          onBack={() => setStep("host")}
          onSubmit={submit}
        />
      )}
      {step === "submitting" && (
        <section className="card">
          <p>Submitting your check-in…</p>
        </section>
      )}
      {step === "confirmation" && (
        <ConfirmationStep
          message={confirmationMessage}
          onDone={resetState}
        />
      )}
    </>
  );
}
