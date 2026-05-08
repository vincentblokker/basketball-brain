"use client";

import { Citations } from "./citations";
import { cn } from "@/lib/utils";
import type { QueryResponse } from "@/lib/types";

type Props = {
  role: "user" | "assistant";
  content: string;
  response?: QueryResponse;
};

export function Message({ role, content, response }: Props) {
  if (role === "user") {
    return (
      <div className="flex">
        <div
          className={cn(
            "ml-auto max-w-[78%]",
            "rounded-tl-[14px] rounded-tr-[14px] rounded-br-[4px] rounded-bl-[14px]",
            "border border-line bg-bg-3 px-4 py-3",
            "text-[15.5px] leading-[1.5] text-fg",
          )}
        >
          {content}
        </div>
      </div>
    );
  }

  if (response?.out_of_scope) {
    return (
      <AssistantWrapper>
        <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-fg-4 mb-2">
          <span aria-hidden className="h-[5px] w-[5px] rounded-full bg-fg-4" />
          Buiten bereik van de bronnen
        </div>
        <p className="italic text-[15px] leading-[1.6] text-fg-3">{content}</p>
      </AssistantWrapper>
    );
  }

  return (
    <AssistantWrapper>
      <div className="bb-prose">
        {content.split("\n\n").map((para, i) => (
          <p key={i} className="mb-3.5 last:mb-0">
            {para}
          </p>
        ))}
      </div>
      {response?.citations?.length ? <Citations items={response.citations} /> : null}
    </AssistantWrapper>
  );
}

function AssistantWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div
      className={cn(
        "relative py-1 pl-[18px]",
        "before:absolute before:left-0 before:top-1.5 before:bottom-1.5 before:w-[2px]",
        "before:rounded-[2px]",
        "before:bg-gradient-to-b before:from-accent before:to-transparent",
      )}
    >
      {children}
    </div>
  );
}
