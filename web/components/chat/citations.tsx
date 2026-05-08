import { Badge } from "@/components/ui/badge";
import type { Citation } from "@/lib/types";

export function Citations({ items }: { items: Citation[] }) {
  if (!items.length) return null;
  const seen = new Set<string>();
  const unique = items.filter((c) => {
    if (seen.has(c.source_id)) return false;
    seen.add(c.source_id);
    return true;
  });
  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {unique.map((c) => (
        <a key={c.chunk_id} href={c.url} target="_blank" rel="noreferrer">
          <Badge
            variant="secondary"
            className="hover:bg-primary hover:text-primary-foreground transition-colors"
          >
            {c.title}
            {c.section ? ` — ${c.section}` : c.page ? ` p.${c.page}` : ""}
          </Badge>
        </a>
      ))}
    </div>
  );
}
