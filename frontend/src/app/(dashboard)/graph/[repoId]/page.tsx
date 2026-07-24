"use client";
import { ArchitectureGraph } from "@/components/graph/ArchitectureGraph";

export default async function GraphPage({ params }: { params: Promise<{ repoId: string }> }) {
  const { repoId } = await params;
  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] space-y-4">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Architecture Graph</h2>
        <p className="text-muted-foreground text-sm mt-1">
          Interactive visualization of your codebase. Click any node to inspect it.
        </p>
      </div>
      <div className="flex-1 rounded-xl border bg-card overflow-hidden">
        <ArchitectureGraph repoId={repoId} />
      </div>
    </div>
  );
}
