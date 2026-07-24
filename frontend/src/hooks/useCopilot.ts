"use client";
import { useState, useCallback } from "react";
import { copilotApi } from "@/lib/api/copilot";
import type { ChatMessage } from "@/types/copilot";

export function useCopilot(repoId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const ask = useCallback(async (question: string, contextNodeId?: string) => {
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: question, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    try {
      const response = await copilotApi.ask(repoId, question, contextNodeId);
      const assistantMsg: ChatMessage = { id: crypto.randomUUID(), role: "assistant", content: response.answer, sources: response.sources, timestamp: new Date() };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      const errMsg: ChatMessage = { id: crypto.randomUUID(), role: "assistant", content: "Sorry, I couldn't process that. Please check your Gemini API key in the backend .env file.", timestamp: new Date() };
      setMessages(prev => [...prev, errMsg]);
    } finally { setLoading(false); }
  }, [repoId]);

  const clear = () => setMessages([]);
  return { messages, loading, ask, clear };
}
