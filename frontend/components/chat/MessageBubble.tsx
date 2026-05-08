"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion } from "framer-motion";
import { Bot, User, ChevronDown, ChevronUp, FileText } from "lucide-react";
import { useState } from "react";
import { cn, formatRelativeTime } from "@/lib/utils";
import { Message } from "@/store/chat";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const [showSources, setShowSources] = useState(false);
  const hasSources = (message.source_documents?.length ?? 0) > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={cn("flex gap-3 px-4 py-2 group", isUser ? "flex-row-reverse" : "flex-row")}
    >
      {/* Avatar */}
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold",
        isUser
          ? "bg-primary text-primary-foreground"
          : "bg-gradient-to-br from-violet-500 to-blue-500 text-white"
      )}>
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Content */}
      <div className={cn("flex flex-col gap-1 max-w-[80%] md:max-w-[70%]", isUser ? "items-end" : "items-start")}>
        <div className={cn(
          "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "bg-primary text-primary-foreground rounded-tr-sm"
            : "bg-muted text-foreground rounded-tl-sm"
        )}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose-chat">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Metadata */}
        <div className={cn("flex items-center gap-2 text-xs text-muted-foreground px-1", isUser ? "flex-row-reverse" : "flex-row")}>
          <span>{formatRelativeTime(message.created_at)}</span>
          {message.model && <span className="opacity-60">· {message.model}</span>}
          {message.latency_ms && <span className="opacity-60">· {message.latency_ms}ms</span>}
        </div>

        {/* Sources */}
        {hasSources && (
          <div className="w-full">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors px-1"
            >
              <FileText className="w-3 h-3" />
              {message.source_documents!.length} source{message.source_documents!.length > 1 ? "s" : ""}
              {showSources ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            {showSources && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="mt-1 space-y-1"
              >
                {message.source_documents!.map((src, i) => (
                  <div key={i} className="bg-background/80 border rounded-lg px-3 py-2 text-xs">
                    <div className="font-medium text-foreground truncate">{src.filename}</div>
                    {src.excerpt && (
                      <p className="text-muted-foreground mt-0.5 line-clamp-2">{src.excerpt}</p>
                    )}
                    {src.score && (
                      <div className="text-primary/70 mt-0.5">Score: {src.score.toFixed(2)}</div>
                    )}
                  </div>
                ))}
              </motion.div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3 px-4 py-2"
    >
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </motion.div>
  );
}
