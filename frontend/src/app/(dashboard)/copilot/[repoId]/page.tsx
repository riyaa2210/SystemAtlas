"use client";
import { use } from "react";
import Link from "next/link";
import { ArrowLeft, Share2, BarChart2 } from "lucide-react";
import { ChatWindow } from "@/components/copilot/ChatWindow";

export default function CopilotPage({ params }: { params: Promise<{ repoId: string }> }) {
  const { repoId } = use(params);
  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] space-y-4">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link href="/repositories" className="text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="w-4 h-4" /></Link>
            <h2 className="text-2xl font-bold tracking-tight">AI Copilot</h2>
          </div>
          <p className="text-muted-foreground text-sm">Ask natural language questions about your codebase.</p>
        </div>
        <div className="flex gap-2">
          <Link href={`/graph/${repoId}`} className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm hover:bg-secondary transition-colors"><Share2 className="w-4 h-4" /> Graph</Link>
          <Link href={`/analytics/${repoId}`} className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm hover:bg-secondary transition-colors"><BarChart2 className="w-4 h-4" /> Analytics</Link>
        </div>
      </div>
      <div className="flex-1 rounded-xl border bg-card p-6 overflow-hidden">
        <ChatWindow repoId={repoId} />
      </div>
    </div>
  );
}
