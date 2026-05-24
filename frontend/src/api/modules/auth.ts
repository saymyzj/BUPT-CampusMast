/**
 * 文件说明：
 * 这是认证模块的 API 封装文件。
 * 负责注册、登录、刷新令牌、获取当前用户等请求。
 * 页面层只需调用这里的函数，无需直接访问 axios。
 */
import apiClient from "@/api/client";
import type {
  AuthPayload,
  AuthRegisterRequest,
  AuthLoginRequest,
  TokenRefreshRequest,
  User,
  UserUpdateRequest,
} from "@/types/api";

/**
 * 注册新用户
 */
export async function register(payload: AuthRegisterRequest): Promise<AuthPayload> {
  const response = await apiClient.post("/api/auth/register", payload);
  return response.data.data;
}

/**
 * 登录
 */
export async function login(payload: AuthLoginRequest): Promise<AuthPayload> {
  const response = await apiClient.post("/api/auth/login", payload);
  return response.data.data;
}

/**
 * 刷新访问令牌
 */
export async function refreshToken(payload: TokenRefreshRequest): Promise<{ accessToken: string }> {
  const response = await apiClient.post("/api/auth/refresh", payload);
  return response.data.data;
}

/**
 * 获取当前用户资料
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get("/api/auth/me");
  return response.data.data;
}

/**
 * 更新当前用户资料
 */
export async function updateCurrentUser(payload: UserUpdateRequest): Promise<User> {
  const response = await apiClient.put("/api/auth/me", payload);
  return response.data.data;
}

