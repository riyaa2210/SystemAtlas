"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, GitBranch, Share2 } from "lucide-react";
import { SystemArchitectureDiagram } from "@/components/architecture/SystemArchitectureDiagram";

/**
 * Standalone full-screen architecture diagram page.
 * Accessible via /architecture/[repoId] — linked from RepoCard and the dashboard.
 * The tabbed detail page (/repositories/[id]) also embeds this diagram inline,
 * so this page is for users who want a full-screen dedicated view.
 */
export default function ArchitecturePage({
  params,
}: {
  params: Promise<{ repoId: string }>;
}) {
  const { repoId } = use(params);

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/repositories"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h2 className="text-2xl font-bold tracking-tight">System Architecture</h2>
          </div>
          <p className="text-muted-foreground text-sm mt-0.5">
            High-level architecture inferred from folder structure, imports, and frameworks.
          </p>
        </div>

        {/* Quick links */}
        <div className="flex items-center gap-2">
          <Link
            href={`/graph/${repoId}`}
            className="inline-flex items-center gap-2 rounded-xl border border-border/60 px-3 py-2 text-sm hover:bg-secondary/80 transition-colors text-muted-foreground hover:text-foreground"
          >
            <GitBranch className="w-4 h-4" />
            Dependency Graph
          </Link>
          <Link
            href={`/repositories/${repoId}`}
            className="inline-flex items-center gap-2 rounded-xl border border-border/60 px-3 py-2 text-sm hover:bg-secondary/80 transition-colors text-muted-foreground hover:text-foreground"
          >
            <Share2 className="w-4 h-4" />
            All Views
          </Link>
        </div>
      </div>

      {/* Diagram — fills remaining height */}
      <div className="flex-1 rounded-xl border bg-card overflow-hidden">
        <SystemArchitectureDiagram repoId={repoId} />
      </div>
    </div>
  );
}
