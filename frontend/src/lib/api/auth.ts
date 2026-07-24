import apiClient from "./client";
import type {
  LoginRequest, RegisterRequest,
  TokenResponse, UserProfile,
} from "@/types/auth";

export const authApi = {
  register: async (data: RegisterRequest): Promise<UserProfile> => {
    const response = await apiClient.post<UserProfile>("/auth/register", data);
    return response.data;
  },

  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/login", data);
    return response.data;
  },

  getMe: async (): Promise<UserProfile> => {
    const response = await apiClient.get<UserProfile>("/auth/me");
    return response.data;
  },

  updateMe: async (name: string): Promise<UserProfile> => {
    const response = await apiClient.put<UserProfile>("/auth/me", { name });
    return response.data;
  },
};
