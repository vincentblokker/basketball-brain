"use client";

import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";
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
  if (!items?.length) return null;
  return (
    <ul
      role="list"
      aria-label="Bronnen"
      className={cn(
        "mt-3.5 flex flex-wrap gap-2",
        "animate-[bb-cite-fade_350ms_ease-out]",
        className,
      )}
    >
      {items.map((c, i) => (
        <li key={c.chunk_id}>
          <a
            href={c.url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Bron ${i + 1}: ${c.title}${formatLocator(c) ? `, ${formatLocator(c)}` : ""} — opent in nieuw tabblad`}
            className={cn(
              "group inline-flex max-w-full items-center gap-2",
              "rounded-md border border-line bg-bg-3 px-2.5 py-1.5",
              "text-[12.5px] text-fg-2",
              "transition-colors duration-150",
              "hover:border-line-2 hover:bg-bg-4 hover:text-fg",
              "focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-2",
            )}
          >
            <span
              aria-hidden
              className="inline-flex h-[18px] w-[18px] items-center justify-center rounded-[4px] bg-accent-soft font-mono text-[10.5px] font-semibold text-accent"
            >
              {i + 1}
            </span>
            <span className="truncate font-medium max-w-[28ch]">
              {c.title}
            </span>
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
        </li>
      ))}
    </ul>
  );
}
