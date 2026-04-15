/**
 * 文件说明：
 * 这是前端路由总表，按冻结文档预置了本项目的核心页面入口。
 * A 同学可以直接在对应页面文件中继续填充实现，默认结构已经覆盖任务大厅、
 * 钱包、通知、地图、聊天和后台页面。
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/tasks" },
  { path: "/login", component: () => import("@/pages/LoginPage.vue") },
  { path: "/register", component: () => import("@/pages/RegisterPage.vue") },
  { path: "/tasks", component: () => import("@/pages/TaskHallPage.vue") },
  { path: "/tasks/new", component: () => import("@/pages/PostTaskPage.vue") },
  { path: "/tasks/:id", component: () => import("@/pages/TaskDetailPage.vue") },
  { path: "/my-tasks", component: () => import("@/pages/MyTasksPage.vue") },
  { path: "/wallet", component: () => import("@/pages/WalletPage.vue") },
  { path: "/profile", component: () => import("@/pages/ProfilePage.vue") },
  { path: "/notifications", component: () => import("@/pages/NotificationsPage.vue") },
  { path: "/chat", component: () => import("@/pages/ChatPage.vue") },
  {
    path: "/map",
    component: () => import("@/pages/CampusMapPage.vue"),
    meta: { layout: "map" },
  },
  { path: "/admin", component: () => import("@/pages/AdminDashboardPage.vue") },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});

