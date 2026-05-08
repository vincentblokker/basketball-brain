import Link from "next/link";
import { MetricsCard } from "@/components/MetricsCard";
import { Separator } from "@/components/ui/separator";

export const metadata = {
  title: "Over Basketball Brain",
  description: "Stack, evaluatie en open-source RAG-systeem zonder Microsoft.",
};

export default function About() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="max-w-3xl mx-auto p-4 flex items-baseline justify-between">
          <Link href="/" className="text-xl font-semibold hover:underline">
            Basketball Brain
          </Link>
          <Link
            href="/"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Chat
          </Link>
        </div>
      </header>

      <article className="max-w-3xl mx-auto p-6 space-y-10">
        <section>
          <h1 className="text-3xl font-bold tracking-tight">Over dit project</h1>
          <p className="text-muted-foreground mt-3 leading-relaxed">
            Basketball Brain is een production-grade Retrieval-Augmented Generation
            systeem over de Nederlandse basketbalwereld — NBB-regels, FIBA-rules,
            talentontwikkeling-onderzoek en coachfilosofie. Volledig gegrond in
            primaire bronnen (geen LLM-gegenereerde inhoud in de kennisbank).
          </p>
          <p className="text-muted-foreground mt-3 leading-relaxed">
            Gebouwd als ADA RAG-eindopdracht én als fundament voor een toekomstige
            ClubDuty-feature. <strong>Geen Microsoft-stack</strong> — open-source van
            embedding tot deploy, zelf-gehost op Hetzner.
          </p>
        </section>

        <Separator />

        <section>
          <h2 className="text-2xl font-semibold mb-4">Evaluatie (RAGAS-stijl)</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <MetricsCard title="Recall@5" value="0.XX" />
            <MetricsCard title="Precision (source)" value="0.XX" />
            <MetricsCard title="Groundedness" value="0.XX" />
          </div>
          <p className="text-sm text-muted-foreground mt-3">
            Gemeten over een handgecureerde 20-vragen-testset (6 lookup, 5
            coachfilosofie, 5 multi-doc, 4 out-of-scope). Cijfers worden ingevuld
            na de finale tuning-iteratie.
          </p>
        </section>

        <Separator />

        <section>
          <h2 className="text-2xl font-semibold mb-4">Stack</h2>
          <ul className="space-y-2 text-sm">
            <li>
              <strong>Backend:</strong> FastAPI + LangChain + ChromaDB + rank_bm25
            </li>
            <li>
              <strong>Embeddings:</strong> bge-m3 (BAAI, MIT) — meertalig, 1024-dim,
              zelf-gehost
            </li>
            <li>
              <strong>Retrieval:</strong> Hybrid search — BM25 + vector + Reciprocal
              Rank Fusion
            </li>
            <li>
              <strong>Indexing-trick:</strong> Contextual Retrieval (Anthropic, sept
              2024) — chunk-prefix via Claude Haiku met prompt caching
            </li>
            <li>
              <strong>LLM:</strong> Claude Sonnet 4.6 via{" "}
              <a
                href="https://openrouter.ai"
                target="_blank"
                rel="noreferrer"
                className="underline"
              >
                OpenRouter
              </a>{" "}
              (model-flexibel, geen vendor-lock-in)
            </li>
            <li>
              <strong>Frontend:</strong> Next.js 16 + Tailwind 4 + shadcn/ui
            </li>
            <li>
              <strong>Hosting:</strong> Hetzner zelf-gehost via Docker-compose +
              Caddy (auto-HTTPS)
            </li>
            <li>
              <strong>Eval:</strong> Hand-curated test set + RAGAS-stijl metrics
            </li>
          </ul>
        </section>

        <Separator />

        <section>
          <h2 className="text-2xl font-semibold mb-4">Bronnen (MVP-corpus)</h2>
          <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
            <li>
              NBB Spelregels 2025-2026 —{" "}
              <a href="https://www.nbb.basketball.nl" className="underline">
                nbb.basketball.nl
              </a>
            </li>
            <li>NBB Talentontwikkeling Richtlijnen</li>
            <li>
              FIBA Official Basketball Rules 2024 —{" "}
              <a href="https://www.fiba.basketball" className="underline">
                fiba.basketball
              </a>
            </li>
            <li>
              &ldquo;Te jong, te snel&rdquo; — Nederlands onderzoek doorschuiven jeugdspelers
            </li>
            <li>
              John Wooden — Pyramid of Success (Wikipedia, fair use)
            </li>
            <li>NL/EN Wikipedia: basketbal-artikelen, shot clock</li>
          </ul>
          <p className="text-sm text-muted-foreground mt-3">
            Alle bronnen primair en publiek. LLMs werden gebruikt om bronnen te
            triangleren, niet om inhoud te genereren.
          </p>
        </section>

        <Separator />

        <section>
          <h2 className="text-2xl font-semibold mb-4">Open</h2>
          <ul className="text-sm space-y-2">
            <li>
              GitHub:{" "}
              <a
                href="https://github.com/vincentblokker/basketball-brain"
                target="_blank"
                rel="noreferrer"
                className="underline"
              >
                github.com/vincentblokker/basketball-brain
              </a>
            </li>
            <li>Licentie: MIT</li>
            <li>
              Auteur:{" "}
              <a href="mailto:vincentblokker@gmail.com" className="underline">
                Vincent Blokker
              </a>
            </li>
          </ul>
        </section>
      </article>
    </main>
  );
}
