"use client";

import { useRef, useState, useCallback, KeyboardEvent } from "react";
import { motion } from "framer-motion";
import { Send, Square, Paperclip } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, isLoading, disabled, placeholder }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, []);

  const handleSend = useCallback(() => {
    const msg = value.trim();
    if (!msg || isLoading) return;
    onSend(msg);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, isLoading, onSend]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t bg-background/80 backdrop-blur-sm px-4 py-3 safe-bottom">
      <div className="max-w-3xl mx-auto">
        <div className={cn(
          "flex items-end gap-2 rounded-2xl border bg-background shadow-lg transition-all",
          "focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/20",
          disabled && "opacity-50"
        )}>
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => { setValue(e.target.value); adjustHeight(); }}
            onKeyDown={handleKeyDown}
            disabled={disabled || isLoading}
            placeholder={placeholder || "Ask me anything about your documents..."}
            rows={1}
            className="flex-1 resize-none bg-transparent px-4 py-3 text-sm leading-6 outline-none placeholder:text-muted-foreground min-h-[44px] max-h-[200px] scrollbar-thin"
          />

          <div className="flex items-center gap-1 pr-2 pb-2">
            <motion.div whileTap={{ scale: 0.9 }}>
              <Button
                size="icon"
                onClick={handleSend}
                disabled={!value.trim() || isLoading || disabled}
                className={cn(
                  "h-8 w-8 rounded-xl transition-all",
                  value.trim() && !isLoading ? "bg-primary hover:bg-primary/90" : "bg-muted text-muted-foreground"
                )}
              >
                {isLoading ? <Square className="h-3.5 w-3.5" /> : <Send className="h-3.5 w-3.5" />}
              </Button>
            </motion.div>
          </div>
        </div>

        <p className="text-center text-xs text-muted-foreground mt-2">
          Press <kbd className="px-1 py-0.5 rounded bg-muted text-xs font-mono">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-muted text-xs font-mono">Shift+Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}
