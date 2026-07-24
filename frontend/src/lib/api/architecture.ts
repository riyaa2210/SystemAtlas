import apiClient from "./client";
import type { ArchitectureData } from "@/types/architecture";

export const architectureApi = {
  getArchitecture: async (repoId: string): Promise<ArchitectureData> => {
    const response = await apiClient.get<ArchitectureData>(`/architecture/${repoId}`);
    return response.data;
  },
};
