"use client";
import { useState, useEffect, useCallback } from "react";
import { architectureApi } from "@/lib/api/architecture";
import type { ArchitectureData } from "@/types/architecture";

export function useArchitecture(repoId: string) {
  const [data, setData] = useState<ArchitectureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await architectureApi.getArchitecture(repoId));
    } catch {
      setError("Failed to load architecture. Ensure the repository has been scanned.");
    } finally {
      setLoading(false);
    }
  }, [repoId]);

  useEffect(() => { fetch(); }, [fetch]);

  return { data, loading, error, refresh: fetch };
}
