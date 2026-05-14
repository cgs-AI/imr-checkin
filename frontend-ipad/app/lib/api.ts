const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type CheckinConfig = {
  site_name: string;
  privacy_text: string;
  consent_text_version: string;
  host_search_min_chars: number;
};

export type VisitorSummary = {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  company: string | null;
  job_title: string | null;
};

export type HostSummary = {
  id: string;
  display_name: string;
  department: string | null;
};

export type VisitorLookupResponse = {
  match: VisitorSummary | null;
  matched_by: string | null;
  ambiguous: boolean;
};

export type VisitSource = "qr_self_checkin" | "ipad_kiosk";

export type CreateVisitRequest = {
  visitor: {
    full_name: string;
    email?: string | null;
    phone?: string | null;
    company?: string | null;
    job_title?: string | null;
  };
  host_id?: string | null;
  host_name_raw?: string | null;
  consent: {
    granted: boolean;
    consent_text_version: string;
    consent_type?: string;
  };
  existing_visitor_id?: string | null;
  source?: VisitSource;
};

export type CreateVisitResponse = {
  visit_id: string;
  visitor_id: string;
  arrived_at: string;
  confirmation_message: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // ignore JSON parse failure
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export const api = {
  getConfig: () => request<CheckinConfig>("/checkin/config"),
  lookupVisitor: (body: { email?: string; phone?: string }) =>
    request<VisitorLookupResponse>("/visitors/lookup", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  searchHosts: (q: string) =>
    request<HostSummary[]>(`/hosts?q=${encodeURIComponent(q)}`),
  submitVisit: (payload: CreateVisitRequest) =>
    request<CreateVisitResponse>("/visits", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
