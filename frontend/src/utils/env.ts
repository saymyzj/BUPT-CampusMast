/**
 * 文件说明：
 * 这是前端环境变量的统一读取封装。
 * 本地验收版前端直接连接本地后端 API 与 WebSocket。
 */
export const appEnv = {
  title: import.meta.env.VITE_APP_TITLE ?? "CampusMast",
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:9000",
  wsBaseUrl: import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:9000/ws",
};
