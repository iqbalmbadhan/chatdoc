import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refreshToken });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          error.config.headers.Authorization = `Bearer ${data.access_token}`;
          return api.request(error.config);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }).then((r) => r.data),
  me: () => api.get("/auth/me").then((r) => r.data),
  changePassword: (current_password: string, new_password: string) =>
    api.post("/auth/change-password", { current_password, new_password }).then((r) => r.data),
};

// ─── Chat ─────────────────────────────────────────────────────────────────────
export const chatApi = {
  send: (body: { message: string; conversation_id?: string; session_id?: string; provider?: string; model?: string }) =>
    api.post("/chat", body).then((r) => r.data),
  conversations: (params?: { page?: number; session_id?: string }) =>
    api.get("/chat/conversations", { params }).then((r) => r.data),
  messages: (convId: string) =>
    api.get(`/chat/conversations/${convId}/messages`).then((r) => r.data),
};

// ─── Documents ────────────────────────────────────────────────────────────────
export const docsApi = {
  upload: (formData: FormData) =>
    api.post("/documents/upload", formData, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data),
  list: (params?: { page?: number; page_size?: number; status?: string }) =>
    api.get("/documents", { params }).then((r) => r.data),
  stats: () => api.get("/documents/stats").then((r) => r.data),
  get: (id: string) => api.get(`/documents/${id}`).then((r) => r.data),
  update: (id: string, body: object) => api.patch(`/documents/${id}`, body).then((r) => r.data),
  reindex: (id: string) => api.post(`/documents/${id}/reindex`).then((r) => r.data),
  delete: (id: string) => api.delete(`/documents/${id}`).then((r) => r.data),
};

// ─── Analytics ────────────────────────────────────────────────────────────────
export const analyticsApi = {
  overview: (days = 30) => api.get("/analytics/overview", { params: { days } }).then((r) => r.data),
  usage: (days = 30) => api.get("/analytics/usage", { params: { days } }).then((r) => r.data),
  visitors: (days = 30) => api.get("/visitors/stats", { params: { days } }).then((r) => r.data),
};

// ─── Providers ────────────────────────────────────────────────────────────────
export const providersApi = {
  list: () => api.get("/providers").then((r) => r.data),
  update: (id: string, body: object) => api.patch(`/providers/${id}`, body).then((r) => r.data),
  models: (name: string) => api.get(`/providers/${name}/models`).then((r) => r.data),
  validate: (name: string) => api.post(`/providers/${name}/validate`).then((r) => r.data),
};

// ─── Keys ─────────────────────────────────────────────────────────────────────
export const keysApi = {
  list: () => api.get("/keys").then((r) => r.data),
  create: (body: { provider: string; key: string; label?: string }) =>
    api.post("/keys", body).then((r) => r.data),
  delete: (id: string) => api.delete(`/keys/${id}`).then((r) => r.data),
};

// ─── Logs ─────────────────────────────────────────────────────────────────────
export const logsApi = {
  chats: (params?: object) => api.get("/logs/chats", { params }).then((r) => r.data),
  system: (params?: object) => api.get("/logs/system", { params }).then((r) => r.data),
  activity: (params?: object) => api.get("/logs/activity", { params }).then((r) => r.data),
  exportChats: () => `${API_URL}/logs/chats/export`,
};

// ─── System ───────────────────────────────────────────────────────────────────
export const systemApi = {
  health: () => api.get("/system/health").then((r) => r.data),
  info: () => api.get("/system/info").then((r) => r.data),
};

// ─── Settings ─────────────────────────────────────────────────────────────────
export const settingsApi = {
  get: () => api.get("/settings").then((r) => r.data),
  update: (body: object) => api.put("/settings", body).then((r) => r.data),
  embeddingProviders: () => api.get("/settings/embedding-providers").then((r) => r.data),
};

// ─── Visitors ─────────────────────────────────────────────────────────────────
export const visitorsApi = {
  track: (body: object) => api.post("/visitors/track", body).then((r) => r.data),
  list: (params?: object) => api.get("/visitors", { params }).then((r) => r.data),
  active: () => api.get("/visitors/active").then((r) => r.data),
};
