"use client";

import { useAuthStore } from "@/lib/store/authStore";
import { authApi } from "@/lib/api/auth";
import { useRouter } from "next/navigation";

export function useAuth() {
  const { token, user, setToken, setUser, logout } = useAuthStore();
  const router = useRouter();

  const signOut = () => {
    logout();
    router.push("/login");
  };

  const refreshUser = async () => {
    try {
      const profile = await authApi.getMe();
      setUser(profile);
    } catch {
      logout();
      router.push("/login");
    }
  };

  return { token, user, signOut, refreshUser, isAuthenticated: !!token };
}
