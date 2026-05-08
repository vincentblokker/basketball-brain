import { Card } from "@/components/ui/card";

type Props = {
  title: string;
  value: string | number;
  suffix?: string;
};

export function MetricsCard({ title, value, suffix }: Props) {
  return (
    <Card className="p-4">
      <div className="text-sm text-muted-foreground">{title}</div>
      <div className="text-3xl font-bold">
        {value}
        {suffix && <span className="text-base ml-1">{suffix}</span>}
      </div>
    </Card>
  );
}
