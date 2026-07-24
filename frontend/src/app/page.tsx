"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store/authStore";

export default function RootPage() {
  const router = useRouter();
  const { token } = useAuthStore();

  useEffect(() => {
    if (token) {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [token, router]);

  return null;
}
