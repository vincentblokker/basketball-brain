const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type Source = {
  id: string;
  file: string;
  title: string;
  content_type: "rule" | "philosophy" | "research" | "general";
  audience: string[];
  age_category: string;
  language: string;
  url: string;
  source_type: "primary" | "synthesized";
  chunk_count: number;
  file_exists: boolean;
  file_bytes: number;
};

export type AddUrlInput = {
  url: string;
  title: string;
  content_type: string;
  audience: string[];
  age_category: string;
  language: string;
};

const STORAGE_KEY = "bbrain.admin.token";

export const adminToken = {
  get: (): string | null => {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(STORAGE_KEY);
  },
  set: (t: string): void => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEY, t);
  },
  clear: (): void => {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(STORAGE_KEY);
  },
};

function authHeaders(): Record<string, string> {
  const t = adminToken.get();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function check(res: Response): Promise<unknown> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

export async function checkAuth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/admin/auth/check`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function listSources(): Promise<Source[]> {
  const data = (await check(await fetch(`${API_BASE}/admin/sources`, { headers: authHeaders() }))) as { sources: Source[] };
  return data.sources;
}

export async function addUrl(input: AddUrlInput): Promise<{ id: string; chunk_count: number }> {
  const res = await fetch(`${API_BASE}/admin/sources/url`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return (await check(res)) as { id: string; chunk_count: number };
}

export async function uploadFile(
  file: File,
  meta: Omit<AddUrlInput, "url"> & { source_url?: string },
): Promise<{ id: string; chunk_count: number }> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("title", meta.title);
  fd.append("content_type", meta.content_type);
  fd.append("audience", meta.audience.join(","));
  fd.append("age_category", meta.age_category);
  fd.append("language", meta.language);
  if (meta.source_url) fd.append("source_url", meta.source_url);
  const res = await fetch(`${API_BASE}/admin/sources/upload`, {
    method: "POST",
    headers: authHeaders(),
    body: fd,
  });
  return (await check(res)) as { id: string; chunk_count: number };
}

export async function deleteSource(id: string): Promise<{ id: string; chunks_deleted: number }> {
  const res = await fetch(`${API_BASE}/admin/sources/${encodeURIComponent(id)}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  return (await check(res)) as { id: string; chunks_deleted: number };
}

export async function reingestSource(id: string): Promise<{ id: string; chunk_count: number }> {
  const res = await fetch(`${API_BASE}/admin/sources/${encodeURIComponent(id)}/reingest`, {
    method: "POST",
    headers: authHeaders(),
  });
  return (await check(res)) as { id: string; chunk_count: number };
}

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}
