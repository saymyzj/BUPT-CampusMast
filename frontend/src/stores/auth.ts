import { defineStore } from "pinia";
import * as authApi from "@/api/modules/auth";
import type { User, AuthRegisterRequest, AuthLoginRequest } from "@/types/api";

function readPersistedUser(): User | null {
  const raw = localStorage.getItem("campusmast.currentUser");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

function persistCurrentUser(user: User | null) {
  if (user) {
    localStorage.setItem("campusmast.currentUser", JSON.stringify(user));
  } else {
    localStorage.removeItem("campusmast.currentUser");
  }
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  currentUser: User | null;
  loading: boolean;
  error: string | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    accessToken: localStorage.getItem("campusmast.accessToken"),
    refreshToken: localStorage.getItem("campusmast.refreshToken"),
    currentUser: readPersistedUser(),
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.currentUser),
    userId: (state) => state.currentUser?.id ?? null,
  },

  actions: {
    async registerUser(payload: AuthRegisterRequest) {
      this.loading = true;
      this.error = null;
      try {
        const result = await authApi.register(payload);
        this.persistTokens(result.accessToken, result.refreshToken);
        this.currentUser = result.user;
        persistCurrentUser(result.user);
        return result.user;
      } catch (err: unknown) {
        this.error = (err as any)?.response?.data?.error?.message || "注册失败";
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async loginUser(payload: AuthLoginRequest) {
      this.loading = true;
      this.error = null;
      try {
        const result = await authApi.login(payload);
        this.persistTokens(result.accessToken, result.refreshToken);
        this.currentUser = result.user;
        persistCurrentUser(result.user);
        return result.user;
      } catch (err: unknown) {
        this.error = (err as any)?.response?.data?.error?.message || "登录失败";
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async fetchCurrentUser() {
      this.loading = true;
      this.error = null;
      try {
        const user = await authApi.getCurrentUser();
        this.currentUser = user;
        persistCurrentUser(user);
        return user;
      } catch (err: unknown) {
        this.error = (err as any)?.response?.data?.error?.message || "获取用户信息失败";
        this.clearTokens();
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async refreshAccessToken() {
      if (!this.refreshToken) {
        this.clearTokens();
        throw new Error("No refresh token");
      }
      try {
        const result = await authApi.refreshToken({ refreshToken: this.refreshToken });
        this.persistTokens(result.accessToken, this.refreshToken);
        return result.accessToken;
      } catch (err: unknown) {
        this.clearTokens();
        throw err;
      }
    },

    async updateCurrentUserProfile(updates: Partial<User>) {
      try {
        const user = await authApi.updateCurrentUser(updates);
        this.currentUser = user;
        return user;
      } catch (err: unknown) {
        this.error = (err as any)?.response?.data?.error?.message || "更新失败";
        throw err;
      }
    },

    persistTokens(accessToken: string, refreshToken: string) {
      this.accessToken = accessToken;
      this.refreshToken = refreshToken;
      localStorage.setItem("campusmast.accessToken", accessToken);
      localStorage.setItem("campusmast.refreshToken", refreshToken);
    },

    clearTokens() {
      this.accessToken = null;
      this.refreshToken = null;
      this.currentUser = null;
      this.error = null;
      localStorage.removeItem("campusmast.accessToken");
      localStorage.removeItem("campusmast.refreshToken");
      persistCurrentUser(null);
    },

    logout() {
      this.clearTokens();
    },
  },
});
