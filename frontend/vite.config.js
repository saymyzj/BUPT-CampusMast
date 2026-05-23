/**
 * 文件说明：
 * 这是前端构建与开发服务器配置文件。
 * 这里预留了路径别名与本地开发端口，方便 A 同学直接接手页面开发与本地联调。
 */
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "node:path";
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        port: 5173,
        host: "0.0.0.0",
        proxy: {
            "/api": {
                target: "http://127.0.0.1:9000",
                changeOrigin: true,
            },
            "/healthz": {
                target: "http://127.0.0.1:9000",
                changeOrigin: true,
            },
        },
    },
});
