"use client";

import { useState } from "react";
import { useAuthStore } from "@/lib/store/authStore";
import { authApi } from "@/lib/api/auth";
import { User, Key, Save, CheckCircle2 } from "lucide-react";

export default function SettingsPage() {
  const { user, setUser } = useAuthStore();
  const [name, setName] = useState(user?.name ?? "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true); setError(null); setSaved(false);
    try {
      const updated = await authApi.updateMe(name);
      setUser(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      setError("Failed to save. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground text-sm mt-1">Manage your account preferences.</p>
      </div>

      {/* Profile */}
      <div className="rounded-xl border bg-card p-6 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <User className="w-4 h-4 text-muted-foreground" />
          <h3 className="font-semibold">Profile</h3>
        </div>

        {error && <div className="rounded-md bg-destructive/10 text-destructive text-sm px-3 py-2">{error}</div>}

        <form onSubmit={handleSave} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              required
              className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Email</label>
            <input
              type="email"
              value={user?.email ?? ""}
              disabled
              className="w-full rounded-md border bg-background px-3 py-2 text-sm text-muted-foreground cursor-not-allowed"
            />
            <p className="text-xs text-muted-foreground">Email cannot be changed.</p>
          </div>
          <button
            type="submit"
            disabled={saving || !name.trim()}
            className="inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {saved ? <CheckCircle2 className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            {saving ? "Saving…" : saved ? "Saved!" : "Save Changes"}
          </button>
        </form>
      </div>

      {/* API Keys info */}
      <div className="rounded-xl border bg-card p-6 space-y-3">
        <div className="flex items-center gap-2 mb-2">
          <Key className="w-4 h-4 text-muted-foreground" />
          <h3 className="font-semibold">API Configuration</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          API keys (Gemini, GitHub) are configured in the backend <code className="font-mono text-xs bg-secondary px-1 py-0.5 rounded">.env</code> file.
        </p>
        <div className="space-y-2 text-sm">
          {[
            { label: "Gemini API Key", url: "https://aistudio.google.com/app/apikey", env: "GEMINI_API_KEY" },
            { label: "GitHub Token", url: "https://github.com/settings/tokens", env: "GITHUB_TOKEN" },
            { label: "Supabase DB URL", url: "https://supabase.com", env: "DATABASE_URL" },
            { label: "Neo4j Aura URI", url: "https://neo4j.com/cloud/platform/aura-graph-database/", env: "NEO4J_URI" },
          ].map(({ label, url, env }) => (
            <div key={env} className="flex items-center justify-between rounded-md bg-secondary/50 px-3 py-2">
              <div>
                <p className="font-medium text-xs">{label}</p>
                <code className="text-xs text-muted-foreground">{env}</code>
              </div>
              <a href={url} target="_blank" rel="noopener noreferrer"
                className="text-xs text-primary hover:underline shrink-0">Get key →</a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
