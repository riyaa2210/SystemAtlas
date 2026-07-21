import apiClient from "./client";
import type { AnalyticsData, RiskItem } from "@/types/analytics";

export const analyticsApi = {
  getAnalytics: async (repoId: string): Promise<AnalyticsData> => {
    const response = await apiClient.get<AnalyticsData>(`/analytics/${repoId}`);
    return response.data;
  },

  getRisks: async (repoId: string): Promise<RiskItem[]> => {
    const response = await apiClient.get<RiskItem[]>(`/analytics/${repoId}/risks`);
    return response.data;
  },
};
