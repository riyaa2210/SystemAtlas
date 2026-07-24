export interface CopilotSource {
  type: string;
  label: string;
  node_id: string | null;
}

export interface CopilotResponse {
  answer: string;
  sources: CopilotSource[];
  question: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: CopilotSource[];
  timestamp: Date;
}
