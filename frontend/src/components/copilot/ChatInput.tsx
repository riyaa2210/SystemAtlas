"use client";
import { useState, useRef, type KeyboardEvent } from "react";
import { Send, Loader2 } from "lucide-react";

const SUGGESTIONS = [
  "Explain the overall architecture",
  "Which modules have the most dependencies?",
  "Are there any circular dependencies?",
  "What frameworks and libraries are used?",
  "Suggest refactoring opportunities",
];

interface ChatInputProps {
  onSend: (message: string) => void;
  loading: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, loading, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || loading || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) { el.style.height = "auto"; el.style.height = `${Math.min(el.scrollHeight, 120)}px`; }
  };

  return (
    <div className="space-y-3 border-t pt-4">
      {/* Suggestion chips */}
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => { setValue(s); textareaRef.current?.focus(); }}
            className="text-xs px-3 py-1.5 rounded-full border hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground">
            {s}
          </button>
        ))}
      </div>

      <div className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask anything about your codebase…"
          disabled={disabled || loading}
          rows={1}
          className="flex-1 resize-none rounded-xl border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground disabled:opacity-50 min-h-[48px] max-h-[120px] leading-relaxed"
        />
        <button
          onClick={handleSend}
          disabled={!value.trim() || loading || disabled}
          className="w-11 h-11 rounded-xl bg-primary text-primary-foreground flex items-center justify-center hover:opacity-90 disabled:opacity-50 transition-opacity shrink-0"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </div>
      <p className="text-xs text-muted-foreground">Press Enter to send, Shift+Enter for new line.</p>
    </div>
  );
}
