"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Message } from "./message";
import { ask } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { QueryResponse } from "@/lib/types";

type Turn =
  | { id: string; role: "user"; content: string }
  | { id: string; role: "assistant"; content: string; response?: QueryResponse }
  | { id: string; role: "assistant-loading" }
  | { id: string; role: "assistant-error"; message: string };

const SUGGESTIONS: { tag: string; text: string }[] = [
  { tag: "REGELS",   text: "Wanneer wordt de 24-secondenklok gereset?" },
  { tag: "JEUGD",    text: "Welk advies bestaat over 12-jarigen die naar U14 doorschuiven?" },
  { tag: "REGELS",   text: "Hoeveel persoonlijke fouten mag een speler maken?" },
  { tag: "COACHING", text: "Wat zegt de literatuur over zone-verdediging onder U14?" },
];

export function Chat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const taRef = useRef<HTMLTextAreaElement>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);
  const isEmpty = turns.length === 0;

  const send = useCallback(async (q: string) => {
    const text = q.trim();
    if (!text) return;
    const userId = crypto.randomUUID();
    const loadingId = crypto.randomUUID();
    setTurns((t) => [
      ...t,
      { id: userId, role: "user", content: text },
      { id: loadingId, role: "assistant-loading" },
    ]);
    setDraft("");

    try {
      const data = await ask(text);
      setTurns((t) =>
        t.map((turn) =>
          turn.id === loadingId
            ? { id: loadingId, role: "assistant", content: data.answer, response: data }
            : turn,
        ),
      );
    } catch {
      setTurns((t) =>
        t.map((turn) =>
          turn.id === loadingId
            ? {
                id: loadingId,
                role: "assistant-error",
                message:
                  "Er ging iets mis bij het ophalen van het antwoord. Probeer het opnieuw — als het blijft gebeuren, laat het weten via GitHub.",
              }
            : turn,
        ),
      );
    }
  }, []);

  useEffect(() => {
    const el = taRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 240) + "px";
  }, [draft]);

  useEffect(() => {
    threadEndRef.current?.scrollTo?.({ top: threadEndRef.current.scrollHeight });
    threadEndRef.current?.parentElement?.scrollTo?.({
      top: threadEndRef.current.parentElement.scrollHeight,
      behavior: "smooth",
    });
  }, [turns.length]);

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send(draft);
    }
  };

  return (
    <div className="flex min-h-[calc(100dvh-72px)] flex-col">
      <div className="flex-1 overflow-hidden">
        <div className="mx-auto max-w-[760px] px-8 pt-10 pb-6">
          {isEmpty ? <Hero /> : <Thread turns={turns} bottomRef={threadEndRef} />}
        </div>
      </div>

      <div
        className={cn(
          isEmpty
            ? "hidden"
            : "sticky bottom-0 border-t border-line bg-gradient-to-b from-transparent to-bg px-8 py-6",
        )}
      >
        <Composer
          inThread
          draft={draft}
          setDraft={setDraft}
          taRef={taRef}
          onKey={onKey}
          onSubmit={() => void send(draft)}
        />
      </div>

      {isEmpty && (
        <div className="mx-auto w-full max-w-[760px] px-8 pb-12">
          <Composer
            draft={draft}
            setDraft={setDraft}
            taRef={taRef}
            onKey={onKey}
            onSubmit={() => void send(draft)}
          />
          <SuggestionGrid onPick={(s) => void send(s)} />
        </div>
      )}
    </div>
  );
}

function Hero() {
  return (
    <div>
      <p className="mb-5 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent before:mr-2.5 before:inline-block before:h-px before:w-[18px] before:align-middle before:bg-accent">
        Kennisbank · Beta
      </p>
      <h1 className="mb-4 text-[52px] font-medium leading-[1.05] tracking-[-0.02em] text-fg [text-wrap:balance] font-serif">
        Vraag het de bron, <span className="italic text-fg-3">niet het internet.</span>
      </h1>
      <p className="mb-9 max-w-[56ch] text-[17px] leading-[1.55] text-fg-2">
        Antwoorden over NBB-spelregels, FIBA-reglementen, talentontwikkeling en
        coachfilosofie — opgehaald uit primaire bronnen, met directe verwijzing
        naar paragraaf en pagina.
      </p>
    </div>
  );
}

function SuggestionGrid({ onPick }: { onPick: (s: string) => void }) {
  return (
    <>
      <p className="mb-3.5 mt-9 text-[11px] font-medium uppercase tracking-[0.14em] text-fg-4">
        Probeer eens
      </p>
      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.text}
            onClick={() => onPick(s.text)}
            className={cn(
              "flex items-start gap-3 rounded-[10px] border border-line",
              "px-4 py-3.5 text-left text-[14px] leading-[1.4] text-fg-2",
              "transition-colors duration-150",
              "hover:border-line-3 hover:bg-bg-3 hover:text-fg",
              "focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent",
            )}
          >
            <span className="mt-px shrink-0 rounded-[4px] bg-bg-3 px-1.5 py-0.5 font-mono text-[10px] font-semibold tracking-wider text-fg-3">
              {s.tag}
            </span>
            {s.text}
          </button>
        ))}
      </div>
    </>
  );
}

function Thread({
  turns,
  bottomRef,
}: {
  turns: Turn[];
  bottomRef: React.RefObject<HTMLDivElement | null>;
}) {
  return (
    <div className="space-y-1">
      {turns.map((turn, i) => {
        const label =
          turn.role === "user"
            ? "Vraag"
            : turn.role === "assistant-loading"
            ? "Antwoord · bronnen ophalen…"
            : "Antwoord";

        const prevRole = turns[i - 1]?.role;
        const showLabel =
          turn.role !== prevRole &&
          !(turn.role === "assistant-error" && prevRole === "user") &&
          !(turn.role === "assistant" && prevRole === "assistant-loading");

        return (
          <div key={turn.id}>
            {showLabel && <TurnLabel>{label}</TurnLabel>}
            {renderTurn(turn)}
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}

function renderTurn(turn: Turn) {
  switch (turn.role) {
    case "user":
      return <Message role="user" content={turn.content} />;
    case "assistant":
      return <Message role="assistant" content={turn.content} response={turn.response} />;
    case "assistant-loading":
      return <LoadingSkeleton />;
    case "assistant-error":
      return <ErrorBlock message={turn.message} />;
  }
}

function TurnLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-8 mb-3.5 flex items-center gap-2.5 text-[11px] font-medium uppercase tracking-[0.18em] text-fg-4 first:mt-0 after:h-px after:flex-1 after:bg-line after:content-['']">
      {children}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="relative py-1 pl-[18px] before:absolute before:left-0 before:top-1.5 before:bottom-1.5 before:w-[2px] before:rounded-[2px] before:bg-gradient-to-b before:from-accent before:to-transparent">
      <div className="bb-skeleton h-3.5 w-[92%] my-2" />
      <div className="bb-skeleton h-3.5 w-[78%] my-2" />
      <div className="bb-skeleton h-3.5 w-[60%] my-2" />
      <div className="mt-3.5 flex gap-2">
        <div className="bb-skeleton h-[30px] w-[180px]" />
        <div className="bb-skeleton h-[30px] w-[180px]" />
      </div>
    </div>
  );
}

function ErrorBlock({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="relative py-1 pl-[18px] before:absolute before:left-0 before:top-1.5 before:bottom-1.5 before:w-[2px] before:rounded-[2px] before:bg-[#f06c5d]/60"
    >
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[#f06c5d]">
        Probleem
      </div>
      <p className="text-[15px] leading-[1.6] text-fg-2">{message}</p>
    </div>
  );
}

function Composer({
  inThread,
  draft,
  setDraft,
  taRef,
  onKey,
  onSubmit,
}: {
  inThread?: boolean;
  draft: string;
  setDraft: (s: string) => void;
  taRef: React.RefObject<HTMLTextAreaElement | null>;
  onKey: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onSubmit: () => void;
}) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      className={cn(
        "rounded-[14px] border border-line bg-bg-3 px-3.5 pt-3.5 pb-2.5 transition-colors",
        "focus-within:border-line-3",
        !inThread && "shadow-elev",
        inThread && "mx-auto max-w-[760px]",
      )}
    >
      <textarea
        ref={taRef}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={onKey}
        rows={inThread ? 1 : 2}
        placeholder={
          inThread
            ? "Stel een vervolgvraag…"
            : "Stel je vraag — bijvoorbeeld: hoe werkt de 8-secondenregel?"
        }
        className={cn(
          "w-full resize-none border-0 bg-transparent px-1 py-1.5 outline-none",
          "text-[16px] leading-[1.55] text-fg placeholder:text-fg-4",
        )}
      />
      <div className="mt-1 flex items-center justify-between border-t border-line pt-2">
        <span className="inline-flex items-center gap-1.5 text-[11.5px] text-fg-4">
          <Kbd>Enter</Kbd> verstuurt
          <span className="opacity-50 mx-1">·</span>
          <Kbd>Shift</Kbd>
          <span className="opacity-60">+</span>
          <Kbd>Enter</Kbd> nieuwe regel
        </span>
        <button
          type="submit"
          disabled={!draft.trim()}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-[6px] px-3 py-1.5 pl-3.5",
            "text-[13px] font-semibold",
            "bg-accent text-accent-ink",
            "transition-colors hover:bg-accent-2",
            "disabled:opacity-40 disabled:cursor-not-allowed",
            "active:scale-[0.97] transition-transform duration-100",
          )}
        >
          Vraag
          <ArrowRight className="h-[13px] w-[13px]" strokeWidth={2.4} />
        </button>
      </div>
    </form>
  );
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="font-mono text-[10px] text-fg-3 bg-bg-4 border border-line rounded px-1.5 py-px leading-none">
      {children}
    </kbd>
  );
}
