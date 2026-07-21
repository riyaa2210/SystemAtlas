import { RegisterForm } from "@/components/auth/RegisterForm";
import { Cpu } from "lucide-react";

export default function RegisterPage() {
  return (
    <main className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/4 w-64 h-64 bg-violet-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md space-y-8 relative z-10">
        <div className="text-center space-y-3">
          <div className="flex justify-center">
            <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center glow-sm">
              <Cpu className="w-7 h-7 text-primary" />
            </div>
          </div>
          <div>
            <h1 className="text-3xl font-bold gradient-text">Living Architecture Map</h1>
            <p className="text-muted-foreground text-sm mt-1">Get started for free — no credit card required</p>
          </div>
        </div>

        <RegisterForm />
      </div>
    </main>
  );
}
