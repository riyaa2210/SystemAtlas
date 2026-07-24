"use client";

import { useState } from "react";
import { Plus, RefreshCw, GitBranch, Search } from "lucide-react";
import { useRepositories } from "@/hooks/useRepositories";
import { RepoCard } from "@/components/repositories/RepoCard";
import { AddRepoModal } from "@/components/repositories/AddRepoModal";

export default function RepositoriesPage() {
  const { repositories, loading, error, refresh, addRepo, deleteRepo, triggerScan } = useRepositories();
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch]       = useState("");

  const filtered = repositories.filter(r =>
    r.full_name.toLowerCase().includes(search.toLowerCase()) ||
    (r.description ?? "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Repositories</h2>
          <p className="text-muted-foreground text-sm mt-0.5">Connect and scan your GitHub codebases.</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button onClick={refresh} disabled={loading}
            className="p-2 rounded-xl border border-border/60 hover:bg-secondary/80 transition-colors text-muted-foreground hover:text-foreground" title="Refresh">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-primary text-primary-foreground px-4 py-2 text-sm font-semibold hover:opacity-90 transition-all glow-sm">
            <Plus className="w-4 h-4" /> Add Repository
          </button>
        </div>
      </div>

      {/* Search */}
      {repositories.length > 0 && (
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search repositories…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full rounded-xl border border-border/60 bg-secondary/50 pl-10 pr-4 py-2 text-sm outline-none focus:ring-2 focus:ring-ring transition-all placeholder:text-muted-foreground/50"
          />
        </div>
      )}

      {error && (
        <div className="rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm px-4 py-3">{error}</div>
      )}

      {/* Loading skeletons */}
      {loading && repositories.length === 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1,2,3].map(i => (
            <div key={i} className="rounded-2xl border border-border/60 bg-card/60 p-5 space-y-3">
              <div className="skeleton h-4 w-3/4 rounded-lg" />
              <div className="skeleton h-3 w-1/2 rounded-lg" />
              <div className="flex gap-2">
                <div className="skeleton h-6 w-16 rounded-lg" />
                <div className="skeleton h-6 w-20 rounded-lg" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && repositories.length === 0 && (
        <div className="rounded-2xl border border-dashed border-border/60 p-16 text-center space-y-4">
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-2xl bg-secondary/60 flex items-center justify-center">
              <GitBranch className="w-7 h-7 text-muted-foreground" />
            </div>
          </div>
          <div>
            <p className="font-semibold">No repositories yet</p>
            <p className="text-sm text-muted-foreground mt-1">Add a GitHub repository to start analyzing its architecture.</p>
          </div>
          <button onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-primary text-primary-foreground px-5 py-2.5 text-sm font-semibold hover:opacity-90 transition-all glow-sm">
            <Plus className="w-4 h-4" /> Add your first repository
          </button>
        </div>
      )}

      {/* Grid */}
      {filtered.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map(repo => (
            <RepoCard key={repo.id} repo={repo} onScan={triggerScan} onDelete={deleteRepo} />
          ))}
        </div>
      )}

      {/* No search results */}
      {!loading && repositories.length > 0 && filtered.length === 0 && (
        <p className="text-center text-muted-foreground text-sm py-8">No repositories match &ldquo;{search}&rdquo;</p>
      )}

      <AddRepoModal open={modalOpen} onClose={() => setModalOpen(false)} onAdd={addRepo} />
    </div>
  );
}
