"use client";

import { useState } from "react";
import { X, Github, Loader2, Sparkles } from "lucide-react";

interface AddRepoModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (url: string) => Promise<void>;
}

const EXAMPLES = [
  { label: "FastAPI", url: "https://github.com/fastapi/fastapi" },
  { label: "Next.js", url: "https://github.com/vercel/next.js" },
  { label: "FastAPI Template", url: "https://github.com/tiangolo/full-stack-fastapi-template" },
];

export function AddRepoModal({ open, onClose, onAdd }: AddRepoModalProps) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setError(null);
    setLoading(true);
    try {
      await onAdd(url.trim());
      setUrl("");
      onClose();
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to add repository. Check the URL and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-background/80 backdrop-blur-md" onClick={onClose} />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-md glass rounded-2xl shadow-2xl p-6 space-y-5 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
              <Github className="w-4 h-4 text-primary" />
            </div>
            <div>
              <h2 className="font-bold text-sm">Add Repository</h2>
              <p className="text-xs text-muted-foreground">Connect a public GitHub repo</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-xl hover:bg-secondary/80 transition-colors text-muted-foreground hover:text-foreground">
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm px-4 py-3">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">GitHub Repository URL</label>
            <input
              type="text"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="https://github.com/owner/repository"
              required
              autoFocus
              className="w-full rounded-xl border bg-secondary/50 px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring focus:border-primary/50 transition-all placeholder:text-muted-foreground/50 font-mono"
            />
          </div>

          {/* Quick examples */}
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> Try an example
            </p>
            <div className="grid grid-cols-3 gap-1.5">
              {EXAMPLES.map(({ label, url: exUrl }) => (
                <button key={label} type="button" onClick={() => setUrl(exUrl)}
                  className="text-xs px-2.5 py-2 rounded-xl border border-border/60 hover:border-primary/30 hover:bg-primary/5 hover:text-primary transition-all text-muted-foreground font-medium">
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 rounded-xl border py-2.5 text-sm hover:bg-secondary/80 transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={loading || !url.trim()}
              className="flex-1 rounded-xl bg-primary text-primary-foreground py-2.5 text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-2 glow-sm">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Github className="w-4 h-4" />}
              {loading ? "Adding…" : "Add Repository"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
