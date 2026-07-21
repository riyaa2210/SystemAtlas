import apiClient from "./client";
import type { Repository, ScanJob } from "@/types/repository";

export const repositoriesApi = {
  list: async (): Promise<Repository[]> => {
    const response = await apiClient.get<Repository[]>("/repositories");
    return response.data;
  },

  add: async (github_url: string): Promise<Repository> => {
    const response = await apiClient.post<Repository>("/repositories", { github_url });
    return response.data;
  },

  get: async (id: string): Promise<Repository> => {
    const response = await apiClient.get<Repository>(`/repositories/${id}`);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/repositories/${id}`);
  },

  triggerScan: async (id: string): Promise<ScanJob> => {
    const response = await apiClient.post<ScanJob>(`/repositories/${id}/scan`);
    return response.data;
  },

  listScans: async (id: string): Promise<ScanJob[]> => {
    const response = await apiClient.get<ScanJob[]>(`/repositories/${id}/scan`);
    return response.data;
  },

  getScan: async (repoId: string, jobId: string): Promise<ScanJob> => {
    const response = await apiClient.get<ScanJob>(`/repositories/${repoId}/scan/${jobId}`);
    return response.data;
  },
};
