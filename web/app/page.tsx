import Link from "next/link";
import { Chat } from "@/components/chat/chat";
import { BasketballMark } from "@/components/marks";

export default function Home() {
  return (
    <div className="min-h-dvh bg-bg">
      <header className="flex items-center justify-between border-b border-line px-10 py-5">
        <div className="flex items-center">
          <Link href="/" className="inline-flex items-center gap-3 text-fg">
            <BasketballMark className="h-[22px] w-[22px] text-accent" />
            <span className="text-[16px] font-semibold tracking-[-0.01em]">
              Basketball Brain
              <em className="ml-1 not-italic font-medium text-fg-3">beta</em>
            </span>
          </Link>
          <span className="ml-3.5 hidden border-l border-line-2 pl-3.5 text-[13px] text-fg-3 lg:inline">
            Kennisbank Nederlandse basketbalwereld · gegrond in primaire bronnen
          </span>
        </div>
        <nav className="flex items-center gap-4.5">
          <span
            aria-label="Bronnen actueel"
            className="inline-flex items-center gap-1.5 rounded-full border border-line bg-bg-3 px-2.5 py-1 text-[12px] tracking-wide text-fg-3"
          >
            <span className="h-[5px] w-[5px] rounded-full bg-verified" aria-hidden />
            Bronnen actueel
          </span>
          <Link
            href="/about"
            className="rounded-md px-2.5 py-1.5 text-[14px] font-medium text-fg-2 transition-colors hover:bg-bg-3 hover:text-fg"
          >
            Over
          </Link>
        </nav>
      </header>

      <main>
        <Chat />
      </main>
    </div>
  );
}
