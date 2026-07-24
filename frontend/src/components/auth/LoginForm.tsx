"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, Mail, Lock, ArrowRight } from "lucide-react";
import { authApi } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/store/authStore";

export function LoginForm() {
  const router = useRouter();
  const { setToken, setUser } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const tokenResponse = await authApi.login({ email, password });
      setToken(tokenResponse.access_token);
      const profile = await authApi.getMe();
      setUser(profile);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Invalid email or password."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass rounded-2xl p-8 space-y-6 animate-fade-in">
      <div className="space-y-1">
        <h2 className="text-2xl font-bold">Sign in</h2>
        <p className="text-sm text-muted-foreground">Welcome back — let&apos;s explore your architecture.</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm px-4 py-3">
          <span className="shrink-0">⚠</span>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              id="email" type="email" autoComplete="email" required
              value={email} onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-xl border bg-secondary/50 pl-10 pr-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring focus:border-primary/50 transition-all placeholder:text-muted-foreground/50"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              id="password" type="password" autoComplete="current-password" required
              value={password} onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl border bg-secondary/50 pl-10 pr-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring focus:border-primary/50 transition-all placeholder:text-muted-foreground/50"
            />
          </div>
        </div>

        <button
          type="submit" disabled={loading}
          className="w-full flex items-center justify-center gap-2 rounded-xl bg-primary text-primary-foreground py-2.5 text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-all glow-sm"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p className="text-sm text-center text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="text-primary hover:underline font-medium">Create one</Link>
      </p>
    </div>
  );
}
