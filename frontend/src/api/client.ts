/**
 * 文件说明：
 * 这是前端统一的 HTTP 客户端封装。
 * A 同学后续应在这里继续补 JWT 注入、401 处理、统一错误提示等逻辑，而不是在
 * 每个页面里直接裸写 axios。
 */
import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:9000";

export const apiClient = axios.create({
  baseURL,
  timeout: 10000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("campusmast.accessToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;

