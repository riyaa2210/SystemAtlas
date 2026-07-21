/**
 * Axios instance with automatic JWT injection and 401 redirect.
 *
 * In development: calls go through Next.js rewrites → /api/v1/* → backend
 * (zero CORS issues because the request never leaves localhost).
 * In production: set NEXT_PUBLIC_API_URL to your deployed backend URL.
 */
import axios from "axios";

// Use the env var directly — Next.js rewrites handle proxying in dev
const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const apiClient = axios.create({
  baseURL,
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
