/**
 * 文件说明：
 * 这是认证模块的 API 封装占位文件。
 * A 同学后续应按照冻结版 OpenAPI 文档继续补齐登录、注册、刷新令牌、获取当前用户
 * 等请求逻辑，保持页面层只调用这里的函数。
 */
import apiClient from "@/api/client";

export async function fetchCurrentUser() {
  const response = await apiClient.get("/api/auth/me");
  return response.data;
}

