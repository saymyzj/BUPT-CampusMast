import { defineStore } from "pinia";
import * as authApi from "@/api/modules/auth";
import type { User, AuthRegisterRequest, AuthLoginRequest } from "@/types/api";

const TOKEN_KEYS = {
  access: "campusmast.accessToken",
  refresh: "campusmast.refreshToken",
  user: "campusmast.currentUser",
};

function clearLegacyLocalAuth() {
  localStorage.removeItem(TOKEN_KEYS.access);
  localStorage.removeItem(TOKEN_KEYS.refresh);
  localStorage.removeItem(TOKEN_KEYS.user);
}

function readPersistedUser(): User | null {
  const raw = sessionStorage.getItem(TOKEN_KEYS.user);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

function persistCurrentUser(user: User | null) {
  if (user) {
    sessionStorage.setItem(TOKEN_KEYS.user, JSON.stringify(user));
  } else {
    sessionStorage.removeItem(TOKEN_KEYS.user);
  }
  localStorage.removeItem(TOKEN_KEYS.user);
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
    accessToken: sessionStorage.getItem(TOKEN_KEYS.access),
    refreshToken: sessionStorage.getItem(TOKEN_KEYS.refresh),
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
        persistCurrentUser(user);
        return user;
      } catch (err: unknown) {
        this.error = (err as any)?.response?.data?.error?.message || "更新失败";
        throw err;
      }
    },

    persistTokens(accessToken: string, refreshToken: string) {
      this.accessToken = accessToken;
      this.refreshToken = refreshToken;
      sessionStorage.setItem(TOKEN_KEYS.access, accessToken);
      sessionStorage.setItem(TOKEN_KEYS.refresh, refreshToken);
      clearLegacyLocalAuth();
    },

    clearTokens() {
      this.accessToken = null;
      this.refreshToken = null;
      this.currentUser = null;
      this.error = null;
      sessionStorage.removeItem(TOKEN_KEYS.access);
      sessionStorage.removeItem(TOKEN_KEYS.refresh);
      clearLegacyLocalAuth();
      persistCurrentUser(null);
    },

    logout() {
      this.clearTokens();
    },
  },
});
