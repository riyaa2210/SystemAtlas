/**
 * Axios instance.
 *
 * Always uses relative URL /api/v1/* so requests go through
 * the Next.js rewrite proxy → backend. This means the browser
 * NEVER makes a cross-origin request — CORS is completely eliminated.
 *
 * next.config.ts rewrites /api/v1/* → NEXT_PUBLIC_API_URL/*
 */
import axios from "axios";

const apiClient = axios.create({
  // Relative URL — works in both dev and production via Next.js rewrites
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
  withCredentials: false,
});

// Inject JWT from Zustand persisted store on every request
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    try {
      const raw = localStorage.getItem("lam_auth");
      if (raw) {
        const parsed = JSON.parse(raw);
        const token = parsed?.state?.token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }
    } catch {
      // ignore parse errors
    }
  }
  return config;
});

// Auto-logout on 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("lam_auth");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default apiClient;
