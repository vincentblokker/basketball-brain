"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { ask } from "@/lib/api";
import type { QueryResponse } from "@/lib/types";
import { Message } from "./message";

type Turn = { role: "user" | "assistant"; content: string; response?: QueryResponse };

export function Chat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit() {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setTurns((t) => [...t, { role: "user", content: q }]);
    setLoading(true);
    try {
      const response = await ask(q);
      setTurns((t) => [...t, { role: "assistant", content: response.answer, response }]);
    } catch (err) {
      setTurns((t) => [
        ...t,
        { role: "assistant", content: `Fout: ${(err as Error).message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4 max-w-3xl mx-auto p-6">
      <div className="space-y-3">
        {turns.map((t, i) => (
          <Message key={i} {...t} />
        ))}
        {loading && <Skeleton className="h-24" />}
      </div>
      <div className="flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Stel je basketbalvraag — over regels, training, of talentontwikkeling…"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void submit();
            }
          }}
          rows={2}
          className="resize-none"
        />
        <Button onClick={submit} disabled={loading}>
          Vraag
        </Button>
      </div>
    </div>
  );
}
