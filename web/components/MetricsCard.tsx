import { cn } from "@/lib/utils";

type Props = {
  title: string;
  value: string | number;
  suffix?: string;
  caption?: string;
  className?: string;
};

export function MetricsCard({ title, value, suffix, caption, className }: Props) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-[14px] border border-line bg-bg-3 px-5 pt-5 pb-5",
        "before:absolute before:inset-x-0 before:top-0 before:h-px",
        "before:bg-[linear-gradient(to_right,transparent,var(--color-accent-edge),transparent)]",
        className,
      )}
    >
      <p className="mb-4 font-mono text-[11px] font-medium tracking-wide text-fg-3">
        {title}
      </p>
      <div className="font-serif text-[44px] font-medium leading-none tracking-[-0.02em] text-fg flex items-baseline gap-1.5">
        {value}
        {suffix && (
          <span className="font-sans text-[14px] font-medium text-fg-3 tracking-normal">
            {suffix}
          </span>
        )}
      </div>
      {caption && (
        <p className="mt-3 text-[12px] leading-[1.4] text-fg-4">{caption}</p>
      )}
    </div>
  );
}
