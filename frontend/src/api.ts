import { SSEEvent, SSEParser } from "./sse";

export interface Finding {
  severity: Severity;
  line: number | null;
  title: string;
  suggestion: string;
}
export type Severity = "critical" | "high" | "medium" | "low" | "info";

export interface ReviewSummary {
  id: number;
  title: string;
  language: string;
  status: string;
  created_at: string;
  finding_count: number;
}
export interface ReviewDetail extends Omit<ReviewSummary, "finding_count"> {
  code: string;
  provider: string;
  summary: string;
  findings: Finding[];
}
export interface Usage {
  plan: string;
  period: string;
  used: number;
  limit: number;
  remaining: number;
}
export interface Plan {
  id: string;
  name: string;
  monthly_reviews: number;
  price_usd_month: number;
}
export interface User {
  id: number;
  email: string;
  plan: string;
}

const TOKEN_KEY = "review-desk.token";

export const tokenStore = {
  get: () => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function errorFrom(res: Response): Promise<ApiError> {
  let message = res.statusText;
  try {
    const body = await res.json();
    message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
  } catch {
    /* keep statusText */
  }
  return new ApiError(res.status, message);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = tokenStore.get();
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) throw await errorFrom(res);
  return res.json() as Promise<T>;
}

export const api = {
  signup: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<User>("/auth/me"),
  usage: () => request<Usage>("/usage"),
  plans: () => request<Plan[]>("/plans"),
  upgrade: (plan: string) =>
    request<{ plan: string; status: string }>("/billing/checkout", {
      method: "POST",
      body: JSON.stringify({ plan }),
    }),
  reviews: () => request<ReviewSummary[]>("/reviews"),
  review: (id: number) => request<ReviewDetail>(`/reviews/${id}`),
};

/** POST /api/reviews/stream and call onEvent for every SSE event. Rejects with ApiError on 4xx. */
export async function streamReview(
  body: { title: string; language: string; code: string },
  onEvent: (e: SSEEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const token = tokenStore.get();
  const res = await fetch("/api/reviews/stream", {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  if (!res.ok || !res.body) throw await errorFrom(res);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  const parser = new SSEParser();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    parser.feed(decoder.decode(value, { stream: true })).forEach(onEvent);
  }
}
