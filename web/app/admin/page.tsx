"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { FileImage, Link2, Loader2, LogOut, Pencil, Plus, RefreshCw, Trash2, Upload, X } from "lucide-react";

import { BasketballMark } from "@/components/marks";
import { cn } from "@/lib/utils";
import {
  type AddUrlInput,
  type Job,
  type Source,
  type SourceUpdate,
  addUrl,
  adminToken,
  checkAuth,
  deleteSource,
  formatBytes,
  listSources,
  pollJob,
  regeneratePages,
  reingestSource,
  stageLabel,
  updateSource,
  uploadFile,
} from "@/lib/admin-api";

const CONTENT_TYPES = ["rule", "philosophy", "research", "general"] as const;
const LANGUAGES = ["nl", "en"] as const;
const AGE_CATEGORIES = ["all", "U10", "U12", "U14", "U16", "U18", "senior"] as const;
const AUDIENCES = ["all", "coach", "referee", "parent", "player"] as const;
const AUTHORITIES = ["official", "semi-official", "supplementary"] as const;
const LEVELS = ["n/a", "Mini", "L1", "L2", "L3", "Rookie", "Starter", "All-Star", "MVP"] as const;
const REGIONS = ["international", "NL", "USA", "EU", "other"] as const;
const RULESETS = ["", "FIBA", "NBA", "NCAA"] as const;
const CHUNK_TYPES = ["prose", "rule_article", "drill", "chapter"] as const;
const COMMON_TOPICS = [
  "", "shooting", "passing", "dribbling", "defense", "footwork", "rebounding",
  "press-break", "spacing", "transition", "ball-screen", "zone", "man-to-man",
  "talent-development", "session-planning", "parents", "coaching-philosophy",
] as const;

type Toast = { id: number; kind: "ok" | "err"; text: string };

/** A live job being tracked in the UI. */
type ActiveJob = Job & { label: string };

export default function AdminPage() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [tokenInput, setTokenInput] = useState("");
  const [sources, setSources] = useState<Source[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [activeJobs, setActiveJobs] = useState<ActiveJob[]>([]);
  const [editing, setEditing] = useState<Source | null>(null);

  const toast = useCallback((kind: Toast["kind"], text: string) => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, kind, text }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000);
  }, []);

  useEffect(() => {
    void (async () => {
      const stored = adminToken.get();
      if (!stored) {
        setAuthed(false);
        return;
      }
      const ok = await checkAuth();
      setAuthed(ok);
      if (!ok) adminToken.clear();
    })();
  }, []);

  const refresh = useCallback(async () => {
    try {
      setSources(await listSources());
    } catch (e) {
      toast("err", `Kon bronnen niet laden: ${(e as Error).message}`);
    }
  }, [toast]);

  useEffect(() => {
    if (!authed) return;
    void refresh();
  }, [authed, refresh]);

  /** Track a job: poll until done/error, update progress, refresh list, clean up. */
  const trackJob = useCallback(
    async (jobId: string, label: string) => {
      setActiveJobs((j) => [...j, {
        id: jobId, kind: "url", status: "running", stage: "starting",
        progress: 0, message: "", source_id: null, chunk_count: null,
        error: null, started_at: 0, updated_at: 0, label,
      }]);
      try {
        const final = await pollJob(jobId, (job) => {
          setActiveJobs((all) => all.map((j) => (j.id === jobId ? { ...j, ...job, label } : j)));
        });
        if (final.status === "done") {
          toast("ok", `${label}: ${final.chunk_count ?? "?"} chunks geïndexeerd`);
        } else {
          toast("err", `${label} mislukt: ${final.error ?? final.message}`);
        }
      } catch (e) {
        toast("err", `${label}: ${(e as Error).message}`);
      } finally {
        // Keep terminal state visible briefly, then remove
        setTimeout(() => {
          setActiveJobs((all) => all.filter((j) => j.id !== jobId));
          void refresh();
        }, 2000);
        void refresh();
      }
    },
    [toast, refresh],
  );

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!tokenInput.trim()) return;
    adminToken.set(tokenInput.trim());
    const ok = await checkAuth();
    if (ok) {
      setAuthed(true);
      setTokenInput("");
      toast("ok", "Ingelogd.");
    } else {
      adminToken.clear();
      toast("err", "Onjuiste admin-token.");
    }
  }

  function handleLogout() {
    adminToken.clear();
    setAuthed(false);
    setSources(null);
    toast("ok", "Uitgelogd.");
  }

  async function handleDelete(id: string) {
    if (!confirm(`Bron "${id}" verwijderen? Bijbehorende chunks worden uit ChromaDB gewist.`)) return;
    setBusy(true);
    try {
      const r = await deleteSource(id);
      toast("ok", `Verwijderd. ${r.chunks_deleted} chunks gewist.`);
      await refresh();
    } catch (e) {
      toast("err", `Verwijderen mislukt: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleReingest(source: Source) {
    setBusy(true);
    try {
      const { job_id } = await reingestSource(source.id);
      void trackJob(job_id, `Reingest: ${source.title}`);
    } catch (e) {
      toast("err", `Reingest mislukt: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleRegeneratePages(source: Source) {
    setBusy(true);
    try {
      const r = await regeneratePages(source.id);
      toast("ok", `${source.title}: ${r.page_count} pagina-thumbnails gerenderd.`);
      await refresh();
    } catch (e) {
      toast("err", `Page-render mislukt: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveEdit(updates: SourceUpdate) {
    if (!editing) return;
    setBusy(true);
    try {
      const r = await updateSource(editing.id, updates);
      toast(
        "ok",
        `Bijgewerkt: ${r.updated_fields.length} velden, ${r.chunks_updated} chunks.`,
      );
      setEditing(null);
      await refresh();
    } catch (e) {
      toast("err", `Bijwerken mislukt: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
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

  if (!authed) {
    return (
      <Layout>
        <main className="mx-auto max-w-md px-8 py-20">
          <h1 className="mb-2 font-serif text-[32px] font-medium tracking-[-0.02em] text-fg">
            Admin
          </h1>
          <p className="mb-8 text-[14px] text-fg-3">
            Voer je admin-token in. Wordt lokaal in deze browser bewaard.
          </p>
          <form onSubmit={handleLogin} className="space-y-3">
            <input
              type="password"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              placeholder="ADMIN_TOKEN"
              className="w-full rounded-[10px] border border-line bg-bg-3 px-4 py-3 text-[15px] text-fg outline-none placeholder:text-fg-4 focus:border-line-3"
              autoFocus
            />
            <button
              type="submit"
              disabled={!tokenInput.trim()}
              className="inline-flex w-full items-center justify-center gap-2 rounded-[8px] bg-accent px-4 py-2.5 text-[14px] font-semibold text-accent-ink transition-colors hover:bg-accent-2 disabled:opacity-40"
            >
              Inloggen
            </button>
          </form>
        </main>
        <ToastStack toasts={toasts} />
      </Layout>
    );
  }

  return (
    <Layout onLogout={handleLogout}>
      <main className="mx-auto max-w-[920px] px-8 py-12">
        <div className="mb-8 flex items-baseline justify-between">
          <div>
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent before:mr-2.5 before:inline-block before:h-px before:w-[18px] before:align-middle before:bg-accent">
              Admin · Bronnen
            </p>
            <h1 className="font-serif text-[32px] font-medium tracking-[-0.02em] text-fg">
              Beheer kennisbank
            </h1>
          </div>
          <button
            onClick={() => void refresh()}
            disabled={busy}
            className="inline-flex items-center gap-1.5 rounded-md border border-line bg-bg-3 px-2.5 py-1.5 text-[13px] text-fg-2 hover:border-line-2 hover:text-fg disabled:opacity-50"
          >
            <RefreshCw className={cn("h-[13px] w-[13px]", busy && "animate-spin")} /> Vernieuwen
          </button>
        </div>

        {activeJobs.length > 0 && (
          <div className="mb-6 space-y-3">
            {activeJobs.map((j) => (
              <ProgressBar key={j.id} job={j} />
            ))}
          </div>
        )}

        <SourcesTable
          sources={sources}
          busy={busy}
          onDelete={handleDelete}
          onReingest={handleReingest}
          onEdit={setEditing}
          onRegeneratePages={handleRegeneratePages}
        />

        <div className="my-12 grid grid-cols-1 gap-6 md:grid-cols-2">
          <AddUrlCard
            disabled={busy}
            trackJob={trackJob}
            setBusy={setBusy}
            toast={toast}
          />
          <UploadCard
            disabled={busy}
            trackJob={trackJob}
            setBusy={setBusy}
            toast={toast}
          />
        </div>
      </main>
      {editing && (
        <EditModal
          source={editing}
          onSave={handleSaveEdit}
          onCancel={() => setEditing(null)}
          busy={busy}
        />
      )}
      <ToastStack toasts={toasts} />
    </Layout>
  );
}

/* ─────── sub-components ─────── */

function Layout({ children, onLogout }: { children: React.ReactNode; onLogout?: () => void }) {
  return (
    <div className="min-h-dvh bg-bg">
      <header className="flex items-center justify-between border-b border-line px-10 py-5">
        <Link href="/" className="inline-flex items-center gap-3 text-fg">
          <BasketballMark className="h-[22px] w-[22px] text-accent" />
          <span className="text-[16px] font-semibold tracking-[-0.01em]">
            Basketball Brain
            <em className="ml-1 not-italic font-medium text-fg-3">admin</em>
          </span>
        </Link>
        <nav className="flex items-center gap-3">
          <Link
            href="/"
            className="rounded-md px-2.5 py-1.5 text-[14px] font-medium text-fg-2 transition-colors hover:bg-bg-3 hover:text-fg"
          >
            Chat
          </Link>
          {onLogout && (
            <button
              onClick={onLogout}
              className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[14px] font-medium text-fg-2 hover:bg-bg-3 hover:text-fg"
            >
              <LogOut className="h-[14px] w-[14px]" /> Uitloggen
            </button>
          )}
        </nav>
      </header>
      {children}
    </div>
  );
}

function ProgressBar({ job }: { job: ActiveJob }) {
  const isError = job.status === "error";
  const isDone = job.status === "done";
  const pct = isDone ? 100 : job.progress;
  return (
    <div
      className={cn(
        "rounded-[12px] border p-4",
        isError ? "border-[#f06c5d]/40 bg-[#f06c5d]/5" : "border-line bg-bg-3",
      )}
    >
      <div className="flex items-baseline justify-between gap-3">
        <div className="flex items-center gap-2 text-[13.5px] font-medium text-fg">
          {!isDone && !isError && <Loader2 className="h-[13px] w-[13px] animate-spin text-accent" />}
          {job.label}
        </div>
        <div className="font-mono text-[11px] text-fg-3">{pct}%</div>
      </div>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-bg-4">
        <div
          className={cn(
            "h-full transition-all duration-300 ease-out",
            isError ? "bg-[#f06c5d]" : "bg-accent",
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-2 flex items-baseline justify-between gap-3 text-[12px] text-fg-3">
        <span className="font-mono uppercase tracking-[0.1em] text-fg-4">
          {stageLabel(job.stage)}
        </span>
        <span className="truncate">{job.message}</span>
      </div>
    </div>
  );
}

function SourcesTable({
  sources,
  busy,
  onDelete,
  onReingest,
  onEdit,
  onRegeneratePages,
}: {
  sources: Source[] | null;
  busy: boolean;
  onDelete: (id: string) => void;
  onReingest: (s: Source) => void;
  onEdit: (s: Source) => void;
  onRegeneratePages: (s: Source) => void;
}) {
  if (sources === null) {
    return <div className="text-fg-3">Laden…</div>;
  }
  if (sources.length === 0) {
    return (
      <div className="rounded-[14px] border border-line bg-bg-3 px-6 py-10 text-center text-fg-3">
        Nog geen bronnen. Voeg er eentje toe via URL of upload hieronder.
      </div>
    );
  }
  const totalChunks = sources.reduce((sum, s) => sum + s.chunk_count, 0);
  return (
    <div className="rounded-[14px] border border-line bg-bg-3 overflow-hidden">
      <div className="flex items-center justify-between border-b border-line px-5 py-3 text-[12px] text-fg-3">
        <span>{sources.length} bronnen · {totalChunks} chunks totaal</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[13.5px]">
          <thead>
            <tr className="text-left text-[11px] font-medium uppercase tracking-[0.12em] text-fg-4">
              <th className="px-5 py-2.5 font-medium">Titel</th>
              <th className="px-3 py-2.5 font-medium">Type</th>
              <th className="px-3 py-2.5 font-medium">Taal</th>
              <th className="px-3 py-2.5 font-medium text-right">Chunks</th>
              <th className="px-3 py-2.5 font-medium text-right">Bestand</th>
              <th className="px-5 py-2.5 font-medium text-right">Acties</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.id} className="border-t border-line hover:bg-bg-2">
                <td className="px-5 py-3 align-top">
                  <div className="font-medium text-fg">{s.title}</div>
                  <div className="font-mono text-[11px] text-fg-4">{s.id}</div>
                </td>
                <td className="px-3 py-3 align-top text-fg-2">{s.content_type}</td>
                <td className="px-3 py-3 align-top text-fg-2 uppercase">{s.language}</td>
                <td className="px-3 py-3 align-top text-right font-mono text-fg-2">
                  {s.chunk_count}
                </td>
                <td className="px-3 py-3 align-top text-right font-mono text-[11.5px] text-fg-3">
                  {s.file_exists ? formatBytes(s.file_bytes) : <span className="text-[#f06c5d]">missing</span>}
                </td>
                <td className="px-5 py-3 align-top text-right">
                  <div className="inline-flex items-center gap-1">
                    <button
                      onClick={() => onEdit(s)}
                      disabled={busy}
                      title="Bewerk metadata"
                      className="rounded-md p-1.5 text-fg-3 hover:bg-bg-4 hover:text-fg disabled:opacity-30"
                    >
                      <Pencil className="h-[13px] w-[13px]" />
                    </button>
                    <button
                      onClick={() => onRegeneratePages(s)}
                      disabled={busy || !s.file_exists || !s.file.toLowerCase().endsWith(".pdf")}
                      title={
                        s.file.toLowerCase().endsWith(".pdf")
                          ? `Render pagina-thumbnails (${s.page_count ?? 0} nu)`
                          : "Geen PDF — pagina-thumbnails niet van toepassing"
                      }
                      className="rounded-md p-1.5 text-fg-3 hover:bg-bg-4 hover:text-fg disabled:opacity-30"
                    >
                      <FileImage className="h-[13px] w-[13px]" />
                    </button>
                    <button
                      onClick={() => onReingest(s)}
                      disabled={busy || !s.file_exists}
                      title="Heringest deze bron"
                      className="rounded-md p-1.5 text-fg-3 hover:bg-bg-4 hover:text-fg disabled:opacity-30"
                    >
                      <RefreshCw className="h-[13px] w-[13px]" />
                    </button>
                    <button
                      onClick={() => onDelete(s.id)}
                      disabled={busy}
                      title="Verwijder bron + chunks"
                      className="rounded-md p-1.5 text-fg-3 hover:bg-bg-4 hover:text-[#f06c5d] disabled:opacity-30"
                    >
                      <Trash2 className="h-[13px] w-[13px]" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

type MetaState = {
  contentType: string; setContentType: (v: string) => void;
  language: string; setLanguage: (v: string) => void;
  ageCategory: string; setAgeCategory: (v: string) => void;
  audience: string[]; setAudience: (v: string[]) => void;
  authority: string; setAuthority: (v: string) => void;
  level: string; setLevel: (v: string) => void;
  topic: string; setTopic: (v: string) => void;
  region: string; setRegion: (v: string) => void;
  ruleset: string; setRuleset: (v: string) => void;
  chunkType: string; setChunkType: (v: string) => void;
};

function MetadataFields(p: MetaState) {
  return (
    <div className="space-y-2.5">
      <div className="grid grid-cols-2 gap-2.5">
        <Select label="Type" value={p.contentType} onChange={p.setContentType} options={[...CONTENT_TYPES]} />
        <Select label="Taal" value={p.language} onChange={p.setLanguage} options={[...LANGUAGES]} />
        <Select label="Leeftijd" value={p.ageCategory} onChange={p.setAgeCategory} options={[...AGE_CATEGORIES]} />
        <Select label="Authority" value={p.authority} onChange={p.setAuthority} options={[...AUTHORITIES]} />
        <Select label="Level" value={p.level} onChange={p.setLevel} options={[...LEVELS]} />
        <Select label="Region" value={p.region} onChange={p.setRegion} options={[...REGIONS]} />
        <Select label="Ruleset" value={p.ruleset} onChange={p.setRuleset} options={[...RULESETS]} />
        <Select label="Chunker" value={p.chunkType} onChange={p.setChunkType} options={[...CHUNK_TYPES]} />
      </div>
      <Select label="Topic" value={p.topic} onChange={p.setTopic} options={[...COMMON_TOPICS]} />
      <MultiSelect label="Doelgroep" values={p.audience} onChange={p.setAudience} options={[...AUDIENCES]} />
    </div>
  );
}

function useMeta(): MetaState {
  const [contentType, setContentType] = useState("general");
  const [language, setLanguage] = useState("nl");
  const [ageCategory, setAgeCategory] = useState("all");
  const [audience, setAudience] = useState<string[]>(["all"]);
  const [authority, setAuthority] = useState("supplementary");
  const [level, setLevel] = useState("n/a");
  const [topic, setTopic] = useState("");
  const [region, setRegion] = useState("international");
  const [ruleset, setRuleset] = useState("");
  const [chunkType, setChunkType] = useState("prose");
  return {
    contentType, setContentType, language, setLanguage,
    ageCategory, setAgeCategory, audience, setAudience,
    authority, setAuthority, level, setLevel,
    topic, setTopic, region, setRegion,
    ruleset, setRuleset, chunkType, setChunkType,
  };
}

function AddUrlCard({
  disabled, trackJob, setBusy, toast,
}: {
  disabled: boolean;
  trackJob: (jobId: string, label: string) => Promise<void>;
  setBusy: (b: boolean) => void;
  toast: (kind: Toast["kind"], text: string) => void;
}) {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const meta = useMeta();
  const [submitting, setSubmitting] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim() || !title.trim()) return;
    setSubmitting(true);
    setBusy(true);
    try {
      const input: AddUrlInput = {
        url: url.trim(),
        title: title.trim(),
        content_type: meta.contentType,
        audience: meta.audience,
        age_category: meta.ageCategory,
        language: meta.language,
        authority: meta.authority as AddUrlInput["authority"],
        level: meta.level as AddUrlInput["level"],
        topic: meta.topic,
        region: meta.region,
        ruleset: meta.ruleset,
        chunk_type: meta.chunkType as AddUrlInput["chunk_type"],
      };
      const { job_id } = await addUrl(input);
      void trackJob(job_id, `URL: ${title.trim()}`);
      setUrl("");
      setTitle("");
    } catch (e) {
      toast("err", `URL toevoegen mislukt: ${(e as Error).message}`);
    } finally {
      setSubmitting(false);
      setBusy(false);
    }
  }

  return (
    <Card title="Toevoegen via URL" icon={<Link2 className="h-[15px] w-[15px]" />}>
      <form onSubmit={submit} className="space-y-3">
        <Input label="URL" type="url" value={url} onChange={setUrl} placeholder="https://..." required />
        <Input label="Titel" value={title} onChange={setTitle} placeholder="Bijv. NBB Spelregels 2025-2026" required />
        <MetadataFields {...meta} />
        <button
          type="submit"
          disabled={disabled || submitting || !url.trim() || !title.trim()}
          className="inline-flex w-full items-center justify-center gap-2 rounded-[8px] bg-accent px-4 py-2.5 text-[14px] font-semibold text-accent-ink hover:bg-accent-2 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {submitting ? <Loader2 className="h-[14px] w-[14px] animate-spin" /> : <Plus className="h-[14px] w-[14px]" />}
          Toevoegen + ingest
        </button>
      </form>
    </Card>
  );
}

function UploadCard({
  disabled, trackJob, setBusy, toast,
}: {
  disabled: boolean;
  trackJob: (jobId: string, label: string) => Promise<void>;
  setBusy: (b: boolean) => void;
  toast: (kind: Toast["kind"], text: string) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const meta = useMeta();
  const [submitting, setSubmitting] = useState(false);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function pickFile(f: File | null) {
    setFile(f);
    if (f && !title) {
      setTitle(f.name.replace(/\.[^.]+$/, "").replace(/[-_]/g, " "));
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) pickFile(f);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !title.trim()) return;
    setSubmitting(true);
    setBusy(true);
    try {
      const { job_id } = await uploadFile(file, {
        title: title.trim(),
        content_type: meta.contentType,
        audience: meta.audience,
        age_category: meta.ageCategory,
        language: meta.language,
        authority: meta.authority as AddUrlInput["authority"],
        level: meta.level as AddUrlInput["level"],
        topic: meta.topic,
        region: meta.region,
        ruleset: meta.ruleset,
        chunk_type: meta.chunkType as AddUrlInput["chunk_type"],
      });
      void trackJob(job_id, `Upload: ${title.trim()}`);
      setFile(null);
      setTitle("");
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (e) {
      toast("err", `Upload mislukt: ${(e as Error).message}`);
    } finally {
      setSubmitting(false);
      setBusy(false);
    }
  }

  return (
    <Card title="Bestand uploaden" icon={<Upload className="h-[15px] w-[15px]" />}>
      <form onSubmit={submit} className="space-y-3">
        <label
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={cn(
            "block cursor-pointer rounded-[10px] border-2 border-dashed px-4 py-7 text-center transition-colors",
            dragging ? "border-accent bg-accent-soft" : "border-line bg-bg-3 hover:border-line-3",
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.html,.htm,.md,.txt"
            className="sr-only"
            onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
          />
          {file ? (
            <div>
              <div className="font-medium text-fg">{file.name}</div>
              <div className="mt-1 text-[12px] text-fg-3">{formatBytes(file.size)}</div>
            </div>
          ) : (
            <div className="text-fg-3">
              <Upload className="mx-auto mb-2 h-5 w-5" />
              <div className="text-[14px]">Sleep een bestand hierheen of klik om te kiezen</div>
              <div className="mt-1 text-[11.5px] text-fg-4">PDF, HTML, MD, TXT</div>
            </div>
          )}
        </label>
        <Input label="Titel" value={title} onChange={setTitle} placeholder="Bijv. Te jong te snel" required />
        <MetadataFields {...meta} />
        <button
          type="submit"
          disabled={disabled || submitting || !file || !title.trim()}
          className="inline-flex w-full items-center justify-center gap-2 rounded-[8px] bg-accent px-4 py-2.5 text-[14px] font-semibold text-accent-ink hover:bg-accent-2 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {submitting ? <Loader2 className="h-[14px] w-[14px] animate-spin" /> : <Plus className="h-[14px] w-[14px]" />}
          Upload + ingest
        </button>
      </form>
    </Card>
  );
}

function Card({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-[14px] border border-line bg-bg-3 p-5">
      <div className="mb-4 flex items-center gap-2 text-[14px] font-semibold text-fg">
        <span className="text-accent">{icon}</span>
        {title}
      </div>
      {children}
    </div>
  );
}

function Input({
  label, value, onChange, placeholder, required, type = "text",
}: {
  label: string; value: string; onChange: (v: string) => void;
  placeholder?: string; required?: boolean; type?: string;
}) {
  return (
    <label className="block">
      <div className="mb-1 text-[11px] font-medium uppercase tracking-[0.12em] text-fg-4">{label}</div>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        className="w-full rounded-[8px] border border-line bg-bg-2 px-3 py-2 text-[14px] text-fg outline-none placeholder:text-fg-4 focus:border-line-3"
      />
    </label>
  );
}

function Select({
  label, value, onChange, options,
}: {
  label: string; value: string; onChange: (v: string) => void; options: string[];
}) {
  return (
    <label className="block">
      <div className="mb-1 text-[11px] font-medium uppercase tracking-[0.12em] text-fg-4">{label}</div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-[8px] border border-line bg-bg-2 px-3 py-2 text-[14px] text-fg outline-none focus:border-line-3"
      >
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </label>
  );
}

function MultiSelect({
  label, values, onChange, options,
}: {
  label: string; values: string[]; onChange: (v: string[]) => void; options: string[];
}) {
  function toggle(opt: string) {
    onChange(values.includes(opt) ? values.filter((v) => v !== opt) : [...values, opt]);
  }
  return (
    <label className="block">
      <div className="mb-1 text-[11px] font-medium uppercase tracking-[0.12em] text-fg-4">{label}</div>
      <div className="flex flex-wrap gap-1">
        {options.map((o) => {
          const selected = values.includes(o);
          return (
            <button
              type="button"
              key={o}
              onClick={() => toggle(o)}
              className={cn(
                "rounded-md border px-2 py-0.5 text-[12px] transition-colors",
                selected
                  ? "border-accent-edge bg-accent-soft text-accent"
                  : "border-line bg-bg-2 text-fg-3 hover:border-line-3 hover:text-fg",
              )}
            >
              {o}
            </button>
          );
        })}
      </div>
    </label>
  );
}

function EditModal({
  source,
  onSave,
  onCancel,
  busy,
}: {
  source: Source;
  onSave: (updates: SourceUpdate) => void;
  onCancel: () => void;
  busy: boolean;
}) {
  const [title, setTitle] = useState(source.title);
  const [url, setUrl] = useState(source.url);
  const meta = useMeta();

  // Pre-fill from current source on mount
  useEffect(() => {
    meta.setContentType(source.content_type);
    meta.setLanguage(source.language);
    meta.setAgeCategory(source.age_category);
    meta.setAudience(source.audience.length ? source.audience : ["all"]);
    meta.setAuthority(source.authority ?? "supplementary");
    meta.setLevel(source.level ?? "n/a");
    meta.setTopic(source.topic ?? "");
    meta.setRegion(source.region ?? "international");
    meta.setRuleset(source.ruleset ?? "");
    meta.setChunkType(source.chunk_type ?? "prose");
    // chunkType is editable here for completeness but the backend ignores it
    // (changing chunker post-ingest needs reingest).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source.id]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const updates: SourceUpdate = {
      title: title.trim(),
      url: url.trim(),
      content_type: meta.contentType,
      audience: meta.audience,
      age_category: meta.ageCategory,
      language: meta.language,
      authority: meta.authority as SourceUpdate["authority"],
      level: meta.level as SourceUpdate["level"],
      topic: meta.topic,
      region: meta.region,
      ruleset: meta.ruleset,
    };
    onSave(updates);
  }

  return (
    <div
      className="fixed inset-0 z-40 bg-bg/80 backdrop-blur-sm flex items-start justify-center overflow-y-auto p-4"
      onClick={onCancel}
    >
      <div
        className="my-12 w-full max-w-[640px] rounded-[14px] border border-line bg-bg-3 shadow-elev"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
          <div className="flex items-center gap-2 text-[14px] font-semibold text-fg">
            <span className="text-accent"><Pencil className="h-[15px] w-[15px]" /></span>
            Bewerk metadata
          </div>
          <button
            onClick={onCancel}
            disabled={busy}
            className="rounded-md p-1.5 text-fg-3 hover:bg-bg-4 hover:text-fg disabled:opacity-30"
          >
            <X className="h-[14px] w-[14px]" />
          </button>
        </div>
        <form onSubmit={submit} className="space-y-3 p-5">
          <div className="text-[11px] font-medium uppercase tracking-[0.12em] text-fg-4">ID</div>
          <div className="-mt-2 mb-3 font-mono text-[12px] text-fg-3">{source.id}</div>
          <Input label="Titel" value={title} onChange={setTitle} required />
          <Input label="URL" value={url} onChange={setUrl} />
          <MetadataFields {...meta} />
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onCancel}
              disabled={busy}
              className="flex-1 rounded-[8px] border border-line bg-bg-2 px-4 py-2.5 text-[14px] font-medium text-fg-2 hover:border-line-3 hover:text-fg disabled:opacity-40"
            >
              Annuleren
            </button>
            <button
              type="submit"
              disabled={busy || !title.trim()}
              className="flex-1 inline-flex items-center justify-center gap-2 rounded-[8px] bg-accent px-4 py-2.5 text-[14px] font-semibold text-accent-ink hover:bg-accent-2 disabled:opacity-40"
            >
              {busy ? <Loader2 className="h-[14px] w-[14px] animate-spin" /> : null}
              Opslaan
            </button>
          </div>
          <p className="text-[11.5px] text-fg-4">
            Wijzigingen worden direct toegepast op alle chunks van deze bron in ChromaDB. Geen reingest nodig.
          </p>
        </form>
      </div>
    </div>
  );
}

function ToastStack({ toasts }: { toasts: Toast[] }) {
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          role="status"
          className={cn(
            "pointer-events-auto rounded-[10px] border bg-bg-3 px-4 py-2.5 text-[13.5px] shadow-elev",
            t.kind === "ok" ? "border-line text-fg" : "border-[#f06c5d]/30 text-[#f06c5d]",
          )}
        >
          {t.text}
        </div>
      ))}
    </div>
  );
}
