"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, Mail, Lock, User, ArrowRight } from "lucide-react";
import { authApi } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/store/authStore";

export function RegisterForm() {
  const router = useRouter();
  const { setToken, setUser } = useAuthStore();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await authApi.register({ name, email, password });
      const tokenResponse = await authApi.login({ email, password });
      setToken(tokenResponse.access_token);
      const profile = await authApi.getMe();
      setUser(profile);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass rounded-2xl p-8 space-y-6 animate-fade-in">
      <div className="space-y-1">
        <h2 className="text-2xl font-bold">Create account</h2>
        <p className="text-sm text-muted-foreground">Start visualizing your codebase today.</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm px-4 py-3">
          <span className="shrink-0">⚠</span>{error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {[
          { label: "Name", id: "name", type: "text", icon: User, value: name, onChange: setName, placeholder: "Your name", autoComplete: "name" },
          { label: "Email", id: "email", type: "email", icon: Mail, value: email, onChange: setEmail, placeholder: "you@example.com", autoComplete: "email" },
          { label: "Password", id: "password", type: "password", icon: Lock, value: password, onChange: setPassword, placeholder: "min 8 characters", autoComplete: "new-password" },
        ].map(({ label, id, type, icon: Icon, value, onChange, placeholder, autoComplete }) => (
          <div key={id} className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{label}</label>
            <div className="relative">
              <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                id={id} type={type} required autoComplete={autoComplete}
                value={value} onChange={e => onChange(e.target.value)}
                placeholder={placeholder}
                minLength={id === "password" ? 8 : undefined}
                className="w-full rounded-xl border bg-secondary/50 pl-10 pr-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring focus:border-primary/50 transition-all placeholder:text-muted-foreground/50"
              />
            </div>
          </div>
        ))}

        <button
          type="submit" disabled={loading}
          className="w-full flex items-center justify-center gap-2 rounded-xl bg-primary text-primary-foreground py-2.5 text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-all glow-sm"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="text-sm text-center text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="text-primary hover:underline font-medium">Sign in</Link>
      </p>
    </div>
  );
}
