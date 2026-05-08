import { create } from "zustand";
import { chatApi } from "@/lib/api";
import { generateSessionId } from "@/lib/utils";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  provider?: string;
  model?: string;
  total_tokens?: number;
  estimated_cost?: number;
  latency_ms?: number;
  source_documents?: SourceDoc[];
  created_at: string;
  isStreaming?: boolean;
}

export interface SourceDoc {
  doc_id: string;
  filename: string;
  chunk_index?: number;
  score?: number;
  excerpt?: string;
}

export interface Conversation {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

interface ChatState {
  conversations: Conversation[];
  currentConversationId: string | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  sessionId: string;
  selectedProvider: string | null;
  selectedModel: string | null;

  sendMessage: (content: string) => Promise<void>;
  loadConversations: () => Promise<void>;
  loadMessages: (convId: string) => Promise<void>;
  setConversation: (id: string | null) => void;
  newConversation: () => void;
  setProvider: (provider: string | null) => void;
  setModel: (model: string | null) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversationId: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  sessionId: generateSessionId(),
  selectedProvider: null,
  selectedModel: null,

  sendMessage: async (content: string) => {
    const { currentConversationId, sessionId, selectedProvider, selectedModel } = get();

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };

    set((s) => ({ messages: [...s.messages, userMsg], isLoading: true }));

    try {
      const data = await chatApi.send({
        message: content,
        conversation_id: currentConversationId || undefined,
        session_id: sessionId,
        provider: selectedProvider || undefined,
        model: selectedModel || undefined,
      });

      const aiMsg: Message = {
        ...data.message,
        id: data.message.id || Date.now().toString(),
      };

      set((s) => ({
        messages: [...s.messages, aiMsg],
        currentConversationId: data.conversation_id,
        isLoading: false,
      }));
    } catch (error) {
      set((s) => ({
        messages: [...s.messages, {
          id: Date.now().toString(),
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
          created_at: new Date().toISOString(),
        }],
        isLoading: false,
      }));
    }
  },

  loadConversations: async () => {
    const { sessionId } = get();
    try {
      const data = await chatApi.conversations({ session_id: sessionId });
      set({ conversations: data.items || [] });
    } catch {}
  },

  loadMessages: async (convId: string) => {
    set({ isLoading: true, currentConversationId: convId });
    try {
      const data = await chatApi.messages(convId);
      set({ messages: data.messages || [], isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  setConversation: (id: string | null) => {
    if (id) {
      get().loadMessages(id);
    } else {
      set({ currentConversationId: null, messages: [] });
    }
  },

  newConversation: () => {
    set({ currentConversationId: null, messages: [] });
  },

  setProvider: (provider) => set({ selectedProvider: provider }),
  setModel: (model) => set({ selectedModel: model }),
}));
