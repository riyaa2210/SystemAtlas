/**
 * Zustand store for authentication state.
 * Persists token to localStorage.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserProfile } from "@/types/auth";

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  setToken: (token: string) => void;
  setUser: (user: UserProfile) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,

      setToken: (token) => set({ token }),

      setUser: (user) => set({ user }),

      logout: () => {
        set({ token: null, user: null });
      },
    }),
    {
      name: "lam_auth",
      partialize: (state) => ({ token: state.token, user: state.user }),
    }
  )
);
