"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Activity, BarChart3, Clock, Loader2, LogOut, RefreshCw } from "lucide-react";

import { BasketballMark } from "@/components/marks";
import { cn } from "@/lib/utils";
import {
  type DayCount,
  type EvalRun,
  type Overview,
  type RecentQuery,
  type TopSource,
  getEvalHistory,
  getOverview,
  getQueriesPerDay,
  getRecent,
  getTopSources,
} from "@/lib/metrics-api";

export default function MetricsPage() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [topSources, setTopSources] = useState<TopSource[] | null>(null);
  const [recent, setRecent] = useState<RecentQuery[] | null>(null);
  const [evalHistory, setEvalHistory] = useState<EvalRun[] | null>(null);
  const [perDay, setPerDay] = useState<DayCount[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const [ov, ts, rq, eh, pd] = await Promise.all([
        getOverview(),
        getTopSources(10),
        getRecent(30),
        getEvalHistory(50),
        getQueriesPerDay(14),
      ]);
      setOverview(ov);
      setTopSources(ts);
      setRecent(rq);
      setEvalHistory(eh);
      setPerDay(pd);
      setAuthed(true);
    } catch (e) {
      setError((e as Error).message);
      // 401 = not authed; redirect to login is handled by /admin index
      if ((e as Error).message.includes("401")) {
        setAuthed(false);
      }
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  if (authed === false) {
    return (
      <Layout>
        <main className="mx-auto max-w-md px-8 py-20">
          <h1 className="mb-2 font-serif text-[28px] font-medium text-fg">
            Niet ingelogd
          </h1>
          <p className="text-fg-3">
            Ga naar <Link href="/admin" className="text-accent underline">/admin</Link>{" "}
            om in te loggen.
          </p>
        </main>
      </Layout>
    );
  }

  if (authed === null) {
    return (
      <Layout>
        <div className="flex h-[60dvh] items-center justify-center text-fg-3">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <main className="mx-auto max-w-[1100px] px-8 py-12">
        <div className="mb-8 flex items-baseline justify-between">
          <div>
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent before:mr-2.5 before:inline-block before:h-px before:w-[18px] before:align-middle before:bg-accent">
              Admin · Metrics
            </p>
            <h1 className="font-serif text-[32px] font-medium tracking-[-0.02em] text-fg">
              Dashboard
            </h1>
            <p className="mt-1 text-[13px] text-fg-3">
              Query-volume, retrieval-kwaliteit en eval-historie.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/admin"
              className="rounded-md border border-line bg-bg-3 px-2.5 py-1.5 text-[13px] text-fg-2 hover:border-line-2 hover:text-fg"
            >
              Bronnen
            </Link>
            <button
              onClick={() => void refresh()}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-md border border-line bg-bg-3 px-2.5 py-1.5 text-[13px] text-fg-2 hover:border-line-2 hover:text-fg disabled:opacity-50"
            >
              <RefreshCw className={cn("h-[13px] w-[13px]", busy && "animate-spin")} /> Vernieuwen
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded-[10px] border border-[#f06c5d]/30 bg-[#f06c5d]/5 p-4 text-[13.5px] text-[#f06c5d]">
            {error}
          </div>
        )}

        {/* Stats cards */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-4 mb-8">
          <StatCard
            icon={<Activity className="h-[15px] w-[15px]" />}
            label="Totaal vragen"
            value={overview?.total_queries ?? "—"}
            sub={overview ? `${overview.queries_last_24h} · 24u, ${overview.queries_last_7d} · 7d` : undefined}
          />
          <StatCard
            icon={<Clock className="h-[15px] w-[15px]" />}
            label="Latency (p50)"
            value={overview ? `${Math.round(overview.p50_latency_ms)}ms` : "—"}
            sub={overview ? `p95 ${Math.round(overview.p95_latency_ms)}ms` : undefined}
          />
          <StatCard
            icon={<BarChart3 className="h-[15px] w-[15px]" />}
            label="Avg similarity"
            value={overview ? overview.mean_similarity.toFixed(3) : "—"}
            sub="cos-sim, top-k vector lane"
          />
          <StatCard
            icon={<Activity className="h-[15px] w-[15px]" />}
            label="Out-of-scope rate"
            value={overview ? `${(overview.oos_rate * 100).toFixed(1)}%` : "—"}
            sub={`${overview?.mean_retrieved.toFixed(1) ?? "—"} chunks/query gem.`}
          />
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 mb-8">
          <Card title="Vragen per dag (14d)">
            <PerDayChart data={perDay} />
          </Card>
          <Card title="Top bronnen">
            <TopSourcesList items={topSources} />
          </Card>
        </div>

        <Card title="Eval-historie · improvement after tuning">
          <EvalHistoryTable runs={evalHistory} />
        </Card>

        <div className="mt-6">
          <Card title="Recente vragen">
            <RecentTable items={recent} />
          </Card>
        </div>
      </main>
    </Layout>
  );
}

/* ─── components ─── */

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh bg-bg">
      <header className="flex items-center justify-between border-b border-line px-10 py-5">
        <Link href="/" className="inline-flex items-center gap-3 text-fg">
          <BasketballMark className="h-[22px] w-[22px] text-accent" />
          <span className="text-[16px] font-semibold tracking-[-0.01em]">
            Basketball Brain
            <em className="ml-1 not-italic font-medium text-fg-3">admin · metrics</em>
          </span>
        </Link>
        <nav className="flex items-center gap-3">
          <Link
            href="/"
            className="rounded-md px-2.5 py-1.5 text-[14px] font-medium text-fg-2 hover:bg-bg-3 hover:text-fg"
          >
            Chat
          </Link>
          <Link
            href="/admin"
            className="rounded-md px-2.5 py-1.5 text-[14px] font-medium text-fg-2 hover:bg-bg-3 hover:text-fg"
          >
            Bronnen
          </Link>
          <button
            onClick={() => {
              if (typeof window !== "undefined") {
                window.localStorage.removeItem("bbrain.admin.token");
                window.location.href = "/admin";
              }
            }}
            className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[14px] font-medium text-fg-2 hover:bg-bg-3 hover:text-fg"
          >
            <LogOut className="h-[14px] w-[14px]" /> Uitloggen
          </button>
        </nav>
      </header>
      {children}
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[14px] border border-line bg-bg-3 overflow-hidden">
      <div className="border-b border-line px-5 py-3 text-[12px] font-semibold uppercase tracking-[0.14em] text-fg-3">
        {title}
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function StatCard({
  icon, label, value, sub,
}: { icon: React.ReactNode; label: string; value: string | number; sub?: string }) {
  return (
    <div className="relative overflow-hidden rounded-[14px] border border-line bg-bg-3 px-5 pt-5 pb-5 before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-[linear-gradient(to_right,transparent,var(--color-accent-edge),transparent)]">
      <div className="mb-3 flex items-center gap-2 text-[11px] font-mono uppercase tracking-[0.12em] text-fg-3">
        <span className="text-accent">{icon}</span>
        {label}
      </div>
      <div className="font-serif text-[36px] font-medium leading-none tracking-[-0.02em] text-fg">
        {value}
      </div>
      {sub && <div className="mt-2 text-[11.5px] text-fg-4">{sub}</div>}
    </div>
  );
}

function PerDayChart({ data }: { data: DayCount[] | null }) {
  if (!data) return <div className="text-fg-3 text-sm">Laden…</div>;
  if (data.length === 0) return <div className="text-fg-4 text-sm">Nog geen queries gelogd.</div>;
  const max = Math.max(...data.map((d) => d.count), 1);
  return (
    <div className="space-y-1">
      {data.map((d) => (
        <div key={d.day} className="flex items-center gap-3 text-[12px]">
          <span className="w-[88px] shrink-0 font-mono text-fg-3">{d.day}</span>
          <div className="relative flex-1 h-[18px] rounded-md bg-bg-2 overflow-hidden">
            <div
              className="h-full bg-accent transition-all"
              style={{ width: `${(d.count / max) * 100}%` }}
            />
          </div>
          <span className="w-8 shrink-0 text-right font-mono text-fg-2">{d.count}</span>
        </div>
      ))}
    </div>
  );
}

function TopSourcesList({ items }: { items: TopSource[] | null }) {
  if (!items) return <div className="text-fg-3 text-sm">Laden…</div>;
  if (items.length === 0) return <div className="text-fg-4 text-sm">Nog geen citations gelogd.</div>;
  const max = Math.max(...items.map((i) => i.count), 1);
  return (
    <div className="space-y-1.5">
      {items.map((s) => (
        <div key={s.source_id} className="text-[12.5px]">
          <div className="flex items-baseline justify-between gap-3 mb-1">
            <span className="truncate font-medium text-fg">{s.source_id}</span>
            <span className="font-mono text-fg-3">{s.count}</span>
          </div>
          <div className="h-[6px] rounded-full bg-bg-2 overflow-hidden">
            <div
              className="h-full bg-accent transition-all"
              style={{ width: `${(s.count / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function EvalHistoryTable({ runs }: { runs: EvalRun[] | null }) {
  if (!runs) return <div className="text-fg-3 text-sm">Laden…</div>;
  if (runs.length === 0) {
    return (
      <div className="text-fg-4 text-sm">
        Nog geen eval-runs. Trigger via{" "}
        <code className="font-mono text-[11.5px] bg-bg-2 px-1.5 py-0.5 rounded">
          GET /api/eval/run
        </code>
        ; resultaten verschijnen hier.
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead>
          <tr className="text-left text-[11px] font-medium uppercase tracking-[0.12em] text-fg-4 border-b border-line">
            <th className="pb-2 pr-3">Tijd</th>
            <th className="pb-2 pr-3">Model</th>
            <th className="pb-2 pr-3 text-right">N</th>
            <th className="pb-2 pr-3 text-right">Recall@5</th>
            <th className="pb-2 pr-3 text-right">Precision</th>
            <th className="pb-2 pr-3 text-right">Groundedness</th>
            <th className="pb-2">Notes</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r, i) => (
            <tr key={i} className="border-b border-line last:border-0">
              <td className="py-2 pr-3 text-fg-3 font-mono text-[11.5px]">
                {new Date(r.ts * 1000).toLocaleString("nl-NL", { dateStyle: "short", timeStyle: "short" })}
              </td>
              <td className="py-2 pr-3 text-fg-2 font-mono text-[11.5px]">
                {r.config.llm_model?.split("/").pop() ?? "—"}
              </td>
              <td className="py-2 pr-3 text-right font-mono text-fg-2">{r.n_questions}</td>
              <td className="py-2 pr-3 text-right font-mono text-fg">{r.mean_recall.toFixed(3)}</td>
              <td className="py-2 pr-3 text-right font-mono text-fg">{r.mean_precision.toFixed(3)}</td>
              <td className="py-2 pr-3 text-right font-mono text-fg">{r.groundedness_rate.toFixed(3)}</td>
              <td className="py-2 text-fg-3 text-[12px]">{r.notes ?? ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RecentTable({ items }: { items: RecentQuery[] | null }) {
  if (!items) return <div className="text-fg-3 text-sm">Laden…</div>;
  if (items.length === 0) return <div className="text-fg-4 text-sm">Nog geen queries gelogd.</div>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead>
          <tr className="text-left text-[11px] font-medium uppercase tracking-[0.12em] text-fg-4 border-b border-line">
            <th className="pb-2 pr-3 w-[110px]">Tijd</th>
            <th className="pb-2 pr-3">Vraag</th>
            <th className="pb-2 pr-3 text-right w-[60px]">Chunks</th>
            <th className="pb-2 pr-3 text-right w-[70px]">Sim</th>
            <th className="pb-2 pr-3 text-right w-[80px]">Latency</th>
            <th className="pb-2 pr-3 w-[60px]">Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((q, i) => (
            <tr key={i} className="border-b border-line last:border-0 hover:bg-bg-2">
              <td className="py-2 pr-3 text-fg-3 font-mono text-[11.5px]">
                {new Date(q.ts * 1000).toLocaleString("nl-NL", { dateStyle: "short", timeStyle: "short" })}
              </td>
              <td className="py-2 pr-3 text-fg max-w-md truncate">{q.question}</td>
              <td className="py-2 pr-3 text-right font-mono text-fg-2">{q.retrieved_count}</td>
              <td className="py-2 pr-3 text-right font-mono text-fg-2">
                {q.mean_similarity != null ? q.mean_similarity.toFixed(2) : "—"}
              </td>
              <td className="py-2 pr-3 text-right font-mono text-fg-2">
                {Math.round(q.latency_ms)}ms
              </td>
              <td className="py-2 pr-3">
                {q.error ? (
                  <span className="text-[11.5px] text-[#f06c5d]">err</span>
                ) : q.is_oos ? (
                  <span className="text-[11.5px] text-fg-4">oos</span>
                ) : (
                  <span className="text-[11.5px] text-verified">ok</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
