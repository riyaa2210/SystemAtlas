"use client";
import { useState, useEffect, useCallback } from "react";
import { graphApi } from "@/lib/api/graph";
import type { GraphData, NodeDetail } from "@/types/graph";

export function useGraph(repoId: string) {
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true); setError(null);
    try { setData(await graphApi.getGraph(repoId)); }
    catch { setError("Failed to load graph. Ensure the repository has been scanned."); }
    finally { setLoading(false); }
  }, [repoId]);

  useEffect(() => { fetch(); }, [fetch]);
  return { data, loading, error, refresh: fetch };
}

export function useNodeDetail(repoId: string, nodeId: string | null) {
  const [detail, setDetail] = useState<NodeDetail | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!nodeId) { setDetail(null); return; }
    setLoading(true);
    graphApi.getNodeDetail(repoId, nodeId).then(setDetail).catch(() => setDetail(null)).finally(() => setLoading(false));
  }, [repoId, nodeId]);
  return { detail, loading };
}
