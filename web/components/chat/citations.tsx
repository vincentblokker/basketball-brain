"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, Eye, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { pageImageUrl } from "@/lib/api";
import type { Citation } from "@/lib/types";

type Props = {
  items: Citation[];
  className?: string;
};

function formatLocator(c: Citation): string {
  const parts: string[] = [];
  if (c.section) parts.push(c.section.replace(/^section\s*/i, "sec. "));
  if (c.page != null) parts.push(`p. ${c.page}`);
  return parts.join(" · ");
}

export function Citations({ items, className }: Props) {
  const [viewing, setViewing] = useState<Citation | null>(null);

  if (!items?.length) return null;
  return (
    <>
      <ul
        role="list"
        aria-label="Bronnen"
        className={cn(
          "mt-3.5 flex flex-wrap gap-2",
          "animate-[bb-cite-fade_350ms_ease-out]",
          className,
        )}
      >
        {items.map((c, i) => {
          const imgUrl = pageImageUrl(c.source_id, c.page);
          return (
            <li key={c.chunk_id} className="inline-flex items-stretch">
              <a
                href={c.url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`Bron ${i + 1}: ${c.title}${formatLocator(c) ? `, ${formatLocator(c)}` : ""} — opent in nieuw tabblad`}
                className={cn(
                  "group inline-flex max-w-full items-center gap-2",
                  "border border-line bg-bg-3 px-2.5 py-1.5",
                  "text-[12.5px] text-fg-2",
                  "transition-colors duration-150",
                  "hover:border-line-2 hover:bg-bg-4 hover:text-fg",
                  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-2",
                  imgUrl ? "rounded-l-md border-r-0" : "rounded-md",
                )}
              >
                <span
                  aria-hidden
                  className="inline-flex h-[18px] w-[18px] items-center justify-center rounded-[4px] bg-accent-soft font-mono text-[10.5px] font-semibold text-accent"
                >
                  {i + 1}
                </span>
                <span className="truncate font-medium max-w-[28ch]">{c.title}</span>
                {formatLocator(c) && (
                  <span className="font-mono text-[11px] text-fg-3 whitespace-nowrap">
                    {formatLocator(c)}
                  </span>
                )}
                <ArrowUpRight
                  aria-hidden
                  className="h-[11px] w-[11px] text-fg-4 transition-all duration-150 group-hover:text-fg-2 group-hover:-translate-y-px group-hover:translate-x-px"
                />
              </a>
              {imgUrl && (
                <button
                  onClick={() => setViewing(c)}
                  aria-label={`Bekijk pagina ${c.page} van ${c.title}`}
                  className={cn(
                    "rounded-r-md border border-line border-l-line-2 bg-bg-3 px-2",
                    "text-fg-3 transition-colors duration-150",
                    "hover:border-line-2 hover:bg-bg-4 hover:text-fg",
                    "focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent",
                  )}
                  title={`Bekijk pagina ${c.page}`}
                >
                  <Eye className="h-[12px] w-[12px]" />
                </button>
              )}
            </li>
          );
        })}
      </ul>

      {viewing && (
        <PageImageModal
          citation={viewing}
          onClose={() => setViewing(null)}
        />
      )}
    </>
  );
}

function PageImageModal({
  citation,
  onClose,
}: {
  citation: Citation;
  onClose: () => void;
}) {
  const url = pageImageUrl(citation.source_id, citation.page);
  const [loaded, setLoaded] = useState(false);
  const [errored, setErrored] = useState(false);

  // Close on Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!url) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-bg/85 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-[900px] max-h-[90dvh] overflow-auto rounded-[14px] border border-line bg-bg-3 shadow-elev"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-line bg-bg-3/95 backdrop-blur px-5 py-3 z-10">
          <div className="min-w-0 flex-1">
            <div className="truncate text-[14px] font-semibold text-fg">{citation.title}</div>
            <div className="text-[11.5px] text-fg-3">
              Pagina {citation.page}
              {citation.section ? ` · ${citation.section}` : ""}
              {" · "}
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-fg-2"
              >
                Open originele bron
              </a>
            </div>
          </div>
          <button
            onClick={onClose}
            className="ml-3 shrink-0 rounded-md p-1.5 text-fg-3 hover:bg-bg-4 hover:text-fg"
            aria-label="Sluiten"
          >
            <X className="h-[14px] w-[14px]" />
          </button>
        </div>

        <div className="p-4">
          {!loaded && !errored && (
            <div className="bb-skeleton h-[400px] w-full" />
          )}
          {errored && (
            <div className="rounded-[10px] border border-line bg-bg-2 p-6 text-center text-[14px] text-fg-3">
              Geen pagina-thumbnail beschikbaar voor deze bron.
              {" "}
              <a href={citation.url} target="_blank" rel="noopener noreferrer" className="underline">
                Open de PDF
              </a>{" "}
              om de pagina te bekijken.
            </div>
          )}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={url}
            alt={`Pagina ${citation.page} van ${citation.title}`}
            onLoad={() => setLoaded(true)}
            onError={() => setErrored(true)}
            className={cn(
              "w-full rounded-[8px] bg-white",
              !loaded && "hidden",
            )}
          />
        </div>
      </div>
    </div>
  );
}
