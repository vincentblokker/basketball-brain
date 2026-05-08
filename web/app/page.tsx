import { Chat } from "@/components/chat/chat";

export default function Home() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="max-w-3xl mx-auto p-4">
          <div className="flex items-baseline justify-between">
            <h1 className="text-xl font-semibold">Basketball Brain</h1>
            <a
              href="/about"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Over
            </a>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            AI-kennisbank voor de Nederlandse basketbalwereld. Antwoorden gegrond
            in primaire bronnen.
          </p>
        </div>
      </header>
      <Chat />
    </main>
  );
}
