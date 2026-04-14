/**
 * 文件说明：
 * 这是身份认证状态仓库。
 * 当前只放最小状态与本地令牌读写能力，A 同学后续可在这里补登录、刷新令牌、
 * 当前用户拉取和路由守卫逻辑。
 */
import { defineStore } from "pinia";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    accessToken: localStorage.getItem("campusmast.accessToken"),
    refreshToken: localStorage.getItem("campusmast.refreshToken"),
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
  },
  actions: {
    persistTokens(accessToken: string, refreshToken: string) {
      this.accessToken = accessToken;
      this.refreshToken = refreshToken;
      localStorage.setItem("campusmast.accessToken", accessToken);
      localStorage.setItem("campusmast.refreshToken", refreshToken);
    },
    clearTokens() {
      this.accessToken = null;
      this.refreshToken = null;
      localStorage.removeItem("campusmast.accessToken");
      localStorage.removeItem("campusmast.refreshToken");
    },
  },
});

