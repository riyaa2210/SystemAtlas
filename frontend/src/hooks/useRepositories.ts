/**
 * Hook for repository list management with loading + error state.
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import { repositoriesApi } from "@/lib/api/repositories";
import { useRepoStore } from "@/lib/store/repoStore";
import type { Repository, ScanJob } from "@/types/repository";

export function useRepositories() {
  const { repositories, setRepositories, addRepository, removeRepository } = useRepoStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRepositories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const repos = await repositoriesApi.list();
      setRepositories(repos);
    } catch {
      setError("Failed to load repositories");
    } finally {
      setLoading(false);
    }
  }, [setRepositories]);

  useEffect(() => {
    fetchRepositories();
  }, [fetchRepositories]);

  const addRepo = async (github_url: string): Promise<Repository> => {
    const repo = await repositoriesApi.add(github_url);
    addRepository(repo);
    return repo;
  };

  const deleteRepo = async (id: string): Promise<void> => {
    await repositoriesApi.delete(id);
    removeRepository(id);
  };

  const triggerScan = async (id: string): Promise<ScanJob> => {
    return await repositoriesApi.triggerScan(id);
  };

  return {
    repositories,
    loading,
    error,
    refresh: fetchRepositories,
    addRepo,
    deleteRepo,
    triggerScan,
  };
}
