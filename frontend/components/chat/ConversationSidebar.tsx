"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, MessageSquare, X, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChatStore } from "@/store/chat";
import { cn, formatRelativeTime } from "@/lib/utils";

interface ConversationSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ConversationSidebar({ isOpen, onClose }: ConversationSidebarProps) {
  const { conversations, currentConversationId, loadConversations, setConversation, newConversation } = useChatStore();

  useEffect(() => {
    loadConversations();
  }, []);

  const handleSelect = (id: string) => {
    setConversation(id);
    onClose();
  };

  const handleNew = () => {
    newConversation();
    onClose();
  };

  return (
    <>
      {/* Backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40 z-40 md:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ x: isOpen ? 0 : "-100%" }}
        transition={{ type: "spring", damping: 30, stiffness: 300 }}
        className={cn(
          "fixed left-0 top-0 h-full w-72 bg-sidebar border-r z-50 flex flex-col shadow-xl",
          !isOpen && "pointer-events-none"
        )}
      >
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary" />
            <span className="font-semibold text-sm">ChatDoc</span>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="p-3">
          <Button onClick={handleNew} className="w-full gap-2" size="sm">
            <Plus className="w-4 h-4" /> New Chat
          </Button>
        </div>

        <ScrollArea className="flex-1 px-2">
          <div className="space-y-0.5">
            {conversations.length === 0 && (
              <p className="text-xs text-muted-foreground text-center py-8">No conversations yet</p>
            )}
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => handleSelect(conv.id)}
                className={cn(
                  "w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors group",
                  currentConversationId === conv.id
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "hover:bg-sidebar-accent/50 text-sidebar-foreground"
                )}
              >
                <div className="flex items-start gap-2">
                  <MessageSquare className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 opacity-60" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-xs leading-snug">{conv.title || "New Conversation"}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{formatRelativeTime(conv.updated_at)}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </ScrollArea>
      </motion.aside>
    </>
  );
}
