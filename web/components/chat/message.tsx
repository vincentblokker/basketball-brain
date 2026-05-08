import { Card } from "@/components/ui/card";
import { Citations } from "./citations";
import type { QueryResponse } from "@/lib/types";

type Props = {
  role: "user" | "assistant";
  content: string;
  response?: QueryResponse;
};

export function Message({ role, content, response }: Props) {
  return (
    <Card className={`p-4 ${role === "user" ? "bg-muted" : "bg-card"}`}>
      <div className="text-xs text-muted-foreground mb-1">
        {role === "user" ? "Jij" : "Basketball Brain"}
      </div>
      <div className="whitespace-pre-wrap leading-relaxed">{content}</div>
      {response && <Citations items={response.citations} />}
    </Card>
  );
}
