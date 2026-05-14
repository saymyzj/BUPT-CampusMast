/**
 * 文件说明：
 * 这是前端应用的运行时入口。
 * 负责挂载全局样式、Pinia、Router，并按环境决定是否启用 MSW。
 * A 同学后续可以继续在这里注入权限守卫、全局错误提示或埋点初始化。
 */
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./styles/index.css";
import { maybeEnableMocking } from "./mock/handlers";

async function bootstrap() {
  await maybeEnableMocking();

  const app = createApp(App);
  app.use(createPinia());
  app.use(router);
  app.mount("#app");
}

void bootstrap();

