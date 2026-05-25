/**
 * 文件说明：
 * 这是前端应用的运行时入口。
 * 负责挂载全局样式、Pinia 和 Router。本地验收版前端直接连接本地后端 API。
 */
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./styles/index.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");

