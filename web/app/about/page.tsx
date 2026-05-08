import Link from "next/link";
import { MetricsCard } from "@/components/MetricsCard";
import { BasketballMark } from "@/components/marks";

// Inline GitHub mark — lucide-react@1.x in this project doesn't export Github.
function GithubMark(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
      <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.305-5.466-1.334-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.4 3-.405 1.02.005 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
    </svg>
  );
}

export const metadata = {
  title: "Over Basketball Brain",
  description: "Stack, evaluatie en open-source RAG-systeem zonder Microsoft.",
};

// Real stack — matches the actual implementation, not the design's defaults.
const STACK: { key: string; val: string }[] = [
  { key: "frontend",    val: "Next.js 16 · Tailwind 4 · shadcn/ui" },
  { key: "retrieval",   val: "ChromaDB · BM25 hybrid · RRF fusion" },
  { key: "embeddings",  val: "BAAI/bge-m3 · 1024-dim · self-hosted" },
  { key: "indexing",    val: "Contextual Retrieval (Anthropic, sept 2024)" },
  { key: "generation",  val: "claude-sonnet-4-6 via OpenRouter" },
  { key: "evaluation",  val: "RAGAS · 20-vragen testset" },
  { key: "hosting",     val: "Hetzner ARM64 · docker-compose · Caddy" },
  { key: "license",     val: "MIT · open-source · geen Microsoft" },
];

// Real source corpus — matches api/data/raw/sources.json.
const SOURCES = [
  { num: "01", title: "NBB Spelregels 2025–2026", meta: "Officiële Nederlandse Basketball Bond · publiek · NL", count: "—" },
  { num: "02", title: "NBB Talentontwikkeling Richtlijnen", meta: "NBB · talent-track jeugd · publiek · NL", count: "—" },
  { num: "03", title: "FIBA Official Basketball Rules 2024", meta: "FIBA Central Board · publiek · EN", count: "—" },
  { num: "04", title: "Te jong, te snel — doorschuiven jeugdspelers", meta: "Onderzoek talentontwikkeling · NL", count: "—" },
  { num: "05", title: "John Wooden — Pyramid of Success", meta: "Coachfilosofie · Wikipedia · fair use · EN", count: "—" },
  { num: "06", title: "Wikipedia — Basketbal (NL) en Shot Clock (EN)", meta: "Algemene context · publiek · NL/EN", count: "—" },
];

export default function About() {
  return (
    <div className="min-h-dvh bg-bg">
      <header className="flex items-center justify-between border-b border-line px-10 py-5">
        <Link href="/" className="inline-flex items-center gap-3 text-fg">
          <BasketballMark className="h-[22px] w-[22px] text-accent" />
          <span className="text-[16px] font-semibold tracking-[-0.01em]">
            Basketball Brain
            <em className="ml-1 not-italic font-medium text-fg-3">beta</em>
          </span>
        </Link>
        <Link
          href="/"
          className="rounded-md px-2.5 py-1.5 text-[14px] font-medium text-fg-2 transition-colors hover:bg-bg-3 hover:text-fg"
        >
          Terug naar chat
        </Link>
      </header>

      <main className="mx-auto max-w-[760px] px-8 py-16">
        <p className="mb-4 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent before:mr-2.5 before:inline-block before:h-px before:w-[18px] before:align-middle before:bg-accent">
          Over · Beta
        </p>
        <h1 className="mb-4 font-serif text-[38px] font-medium leading-[1.1] tracking-[-0.02em] text-fg [text-wrap:balance]">
          Een kennisbank voor de Nederlandse basketbalwereld,{" "}
          <span className="italic text-fg-3">getoetst aan de bron.</span>
        </h1>
        <p className="mb-14 max-w-[60ch] text-[17px] leading-[1.6] text-fg-2">
          Basketball Brain is een retrieval-augmented chatbot die antwoord geeft op vragen over NBB-spelregels, FIBA-reglementen, talentontwikkelingsonderzoek en coachfilosofie. Elk antwoord verwijst naar de paragraaf en pagina van de primaire bron — zodat je het zelf kunt nalezen.
        </p>

        <blockquote className="my-7 border-l-2 border-accent-edge pl-5 font-serif italic text-[19px] leading-[1.45] text-fg">
          &ldquo;Niet weer een AI-assistent. Een coach met een klembord — die altijd het regelboek opslaat.&rdquo;
        </blockquote>

        <Section title="Evaluatie · RAGAS">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <MetricsCard title="Recall@5" value="—" caption="Aandeel relevante bronnen in top-5 retrieval. Wordt ingevuld na tuning-iteratie 3." />
            <MetricsCard title="Precision (source)" value="—" caption="Relevantie van top-5. Beweegt mee met chunk-size en hybrid-weights." />
            <MetricsCard title="Groundedness" value="—" caption="Antwoord blijft binnen retrieved context. Heuristic-meting nu, LLM-judge later." />
          </div>
        </Section>

        <Section title="Stack">
          <dl className="grid grid-cols-1 gap-y-px font-mono text-[13px] sm:grid-cols-2 sm:gap-x-6">
            {STACK.map((row) => (
              <div key={row.key} className="flex items-baseline gap-2.5 border-b border-line py-2.5">
                <dt className="min-w-[110px] shrink-0 text-fg-3">{row.key}</dt>
                <dd className="text-fg">{row.val}</dd>
              </div>
            ))}
          </dl>
        </Section>

        <Section title="Bronnen">
          <ul className="flex flex-col gap-px">
            {SOURCES.map((s) => (
              <li
                key={s.num}
                className="flex items-baseline gap-4 border-b border-line px-1 py-3.5 transition-colors hover:bg-bg-2"
              >
                <span className="w-6 shrink-0 font-mono text-[11px] text-fg-4">{s.num}</span>
                <div className="flex-1">
                  <p className="mb-1 text-[15px] font-medium text-fg">{s.title}</p>
                  <p className="text-[12.5px] text-fg-3">{s.meta}</p>
                </div>
                <span className="shrink-0 rounded border border-line bg-bg-3 px-2 py-0.5 font-mono text-[11px] text-fg-3">
                  {s.count} chunks
                </span>
              </li>
            ))}
          </ul>
        </Section>

        <Section title="Wat het niet is">
          <div className="text-[16px] leading-[1.7] text-fg-2 space-y-3.5">
            <p>
              Geen live-uitslagen, geen tactische adviezen voor specifieke wedstrijden, geen vervanging voor een NBB-cursus. Bij elke vraag waar de bronnen geen uitsluitsel geven, antwoordt het systeem expliciet: <em>&ldquo;Ik weet het niet op basis van de beschikbare bronnen.&rdquo;</em>
            </p>
            <p>
              Achtergrond: gebouwd als ADA RAG-eindopdracht en als fundament voor een ClubDuty AI-feature. De hele stack draait open-source, zonder Microsoft-componenten.
            </p>
          </div>
        </Section>

        <footer className="mt-18 flex flex-wrap justify-between gap-3 border-t border-line pt-6 text-[13px] text-fg-3">
          <span>
            © 2026 Vincent Blokker · Onderdeel van{" "}
            <a href="https://clubduty.nl" className="border-b border-line-2 pb-px text-fg-2 transition-colors hover:text-fg hover:border-line-3">
              ClubDuty
            </a>{" "}
            · MIT-licentie
          </span>
          <span className="inline-flex items-center gap-4.5">
            <a
              href="https://github.com/vincentblokker/basketball-brain"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 border-b border-line-2 pb-px text-fg-2 hover:text-fg"
            >
              <GithubMark className="h-[13px] w-[13px]" /> GitHub
            </a>
            <a href="https://brain.clubduty.app" className="border-b border-line-2 pb-px text-fg-2 hover:text-fg">brain.clubduty.app</a>
          </span>
        </footer>
      </main>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="my-14">
      <h2 className="mb-4 border-b border-line pb-3 text-[13px] font-semibold uppercase tracking-[0.16em] text-fg-3">
        {title}
      </h2>
      {children}
    </section>
  );
}
