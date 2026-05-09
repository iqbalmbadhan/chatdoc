"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, Moon, Sun, Settings, Bot } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { ChatInput } from "@/components/chat/ChatInput";
import { MessageBubble, TypingIndicator } from "@/components/chat/MessageBubble";
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { useChatStore } from "@/store/chat";
import { visitorsApi } from "@/lib/api";
import Link from "next/link";

export default function ChatPage() {
  const { messages, isLoading, sendMessage } = useChatStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, setTheme } = useTheme();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Track visitor
    visitorsApi.track({
      language: navigator.language,
      screen_resolution: `${screen.width}x${screen.height}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      referrer: document.referrer,
      landing_page: window.location.pathname,
    }).catch(() => { });
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <ConversationSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-3 border-b bg-background/80 backdrop-blur-sm safe-top sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <Button variant="ghost" className="gap-2 px-2" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <Menu className="w-4 h-4" />
              <span className="text-xs font-medium hidden lg:block">History</span>
            </Button>
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold text-sm hidden sm:block">ChatDoc</span>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} className="h-8 w-8">
              {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
            <Link href="/admin">
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Settings className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {isEmpty ? (
            <WelcomeScreen />
          ) : (
            <div className="max-w-3xl mx-auto py-4">
              <AnimatePresence initial={false}>
                {messages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
              </AnimatePresence>
              {isLoading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <ChatInput onSend={sendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}

function WelcomeScreen() {
  const suggestions = [
    "Summarize the key points from my documents",
    "What are the main topics covered?",
    "Find information about pricing",
    "Explain the terms and conditions",
  ];
  const { sendMessage } = useChatStore();

  return (
    <div className="flex flex-col items-center justify-center h-full px-4 text-center">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center mx-auto mb-4 shadow-lg">
          <Bot className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold mb-2">ChatDoc AI</h1>
        <p className="text-muted-foreground max-w-sm mb-8 text-sm">
          Ask anything about your uploaded documents. I&apos;ll find the answers with citations.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-md">
          {suggestions.map((s, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.05 }}
              onClick={() => sendMessage(s)}
              className="text-left px-4 py-3 rounded-xl border bg-card hover:bg-accent hover:border-primary/30 transition-all text-sm text-foreground group"
            >
              <span className="text-primary group-hover:translate-x-0.5 inline-block transition-transform">→</span>{" "}
              {s}
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
