"use client";
import { User, Bot, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types/copilot";

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      <div className={cn("w-8 h-8 rounded-full shrink-0 flex items-center justify-center", isUser ? "bg-primary" : "bg-secondary")}>
        {isUser ? <User className="w-4 h-4 text-primary-foreground" /> : <Bot className="w-4 h-4 text-muted-foreground" />}
      </div>
      <div className={cn("max-w-[80%] space-y-1", isUser ? "items-end" : "items-start")}>
        <div className={cn("rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap", isUser ? "bg-primary text-primary-foreground rounded-tr-sm" : "bg-secondary text-foreground rounded-tl-sm")}>
          {message.content}
        </div>
        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-1 px-1">
            {message.sources.map((s, i) => (
              <span key={i} className="text-xs text-muted-foreground bg-secondary px-2 py-0.5 rounded-full flex items-center gap-1">
                <ExternalLink className="w-2.5 h-2.5" />
                {s.label}
              </span>
            ))}
          </div>
        )}
        <p className="text-xs text-muted-foreground px-1">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
    </div>
  );
}
