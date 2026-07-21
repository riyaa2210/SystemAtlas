import apiClient from "./client";
import type { CopilotResponse } from "@/types/copilot";

export const copilotApi = {
  ask: async (repo_id: string, question: string, context_node_id?: string): Promise<CopilotResponse> => {
    const response = await apiClient.post<CopilotResponse>("/copilot/ask", {
      repo_id,
      question,
      context_node_id: context_node_id ?? null,
    });
    return response.data;
  },
};
