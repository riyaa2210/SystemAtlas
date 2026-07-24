"use client";
import { useState, useEffect, useCallback } from "react";
import { analyticsApi } from "@/lib/api/analytics";
import type { AnalyticsData, RiskItem } from "@/types/analytics";

export function useAnalytics(repoId: string) {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [risks, setRisks] = useState<RiskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [a, r] = await Promise.all([analyticsApi.getAnalytics(repoId), analyticsApi.getRisks(repoId)]);
      setAnalytics(a); setRisks(r);
    } catch { setError("No analytics found. Scan the repository first."); }
    finally { setLoading(false); }
  }, [repoId]);

  useEffect(() => { fetch(); }, [fetch]);
  return { analytics, risks, loading, error, refresh: fetch };
}
