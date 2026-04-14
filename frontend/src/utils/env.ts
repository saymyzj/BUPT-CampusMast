/**
 * 文件说明：
 * 这是前端环境变量的统一读取封装。
 * 统一从这里暴露配置，能减少页面里直接散落读取 import.meta.env 的情况。
 */
export const appEnv = {
  title: import.meta.env.VITE_APP_TITLE ?? "CampusMast",
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:9000",
  wsBaseUrl: import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:9000/ws",
  enableMsw: String(import.meta.env.VITE_ENABLE_MSW) === "true",
};

