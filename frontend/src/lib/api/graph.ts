import apiClient from "./client";
import type { GraphData, NodeDetail } from "@/types/graph";

export const graphApi = {
  getGraph: async (repoId: string): Promise<GraphData> => {
    const response = await apiClient.get<GraphData>(`/graph/${repoId}`);
    return response.data;
  },

  getNodeDetail: async (repoId: string, nodeId: string): Promise<NodeDetail> => {
    const response = await apiClient.get<NodeDetail>(`/graph/${repoId}/node/${nodeId}`);
    return response.data;
  },
};
