const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const STORAGE_KEY = "bbrain.admin.token";

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const t = window.localStorage.getItem(STORAGE_KEY);
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function check<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export type Overview = {
  total_queries: number;
  queries_last_24h: number;
  queries_last_7d: number;
  mean_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  mean_similarity: number;
  oos_rate: number;
  mean_retrieved: number;
};

export type TopSource = { source_id: string; count: number };

export type RecentQuery = {
  ts: number;
  question: string;
  retrieved_count: number;
  citation_source_ids: string[];
  answer_length: number;
  is_oos: boolean;
  mean_similarity: number | null;
  latency_ms: number;
  llm_model: string;
  error: string | null;
};

export type EvalRun = {
  ts: number;
  config: Record<string, string>;
  n_questions: number;
  mean_recall: number;
  mean_precision: number;
  groundedness_rate: number;
  notes: string | null;
};

export type DayCount = { day: string; count: number };

export async function getOverview(): Promise<Overview> {
  return check<Overview>(
    await fetch(`${API_BASE}/admin/metrics/overview`, { headers: authHeaders() }),
  );
}

export async function getTopSources(limit = 10): Promise<TopSource[]> {
  const res = await check<{ sources: TopSource[] }>(
    await fetch(`${API_BASE}/admin/metrics/top-sources?limit=${limit}`, {
      headers: authHeaders(),
    }),
  );
  return res.sources;
}

export async function getRecent(limit = 50): Promise<RecentQuery[]> {
  const res = await check<{ queries: RecentQuery[] }>(
    await fetch(`${API_BASE}/admin/metrics/recent?limit=${limit}`, {
      headers: authHeaders(),
    }),
  );
  return res.queries;
}

export async function getEvalHistory(limit = 50): Promise<EvalRun[]> {
  const res = await check<{ runs: EvalRun[] }>(
    await fetch(`${API_BASE}/admin/metrics/eval-history?limit=${limit}`, {
      headers: authHeaders(),
    }),
  );
  return res.runs;
}

export async function getQueriesPerDay(days = 14): Promise<DayCount[]> {
  const res = await check<{ days: DayCount[] }>(
    await fetch(`${API_BASE}/admin/metrics/queries-per-day?days=${days}`, {
      headers: authHeaders(),
    }),
  );
  return res.days;
}
