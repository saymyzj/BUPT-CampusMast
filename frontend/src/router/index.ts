/**
 * 文件说明：
 * 这是前端路由配置文件，包含页面路由和权限守卫。
 * 守卫确保未认证用户不能访问受保护页面。
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/tasks" },
  { path: "/login", component: () => import("@/pages/LoginPage.vue"), meta: { layout: "auth", requiresAuth: false } },
  { path: "/register", component: () => import("@/pages/RegisterPage.vue"), meta: { layout: "auth", requiresAuth: false } },
  { path: "/tasks", component: () => import("@/pages/TaskHallPage.vue"), meta: { requiresAuth: true } },
  { path: "/tasks/new", component: () => import("@/pages/PostTaskPage.vue"), meta: { requiresAuth: true } },
  { path: "/tasks/:id", component: () => import("@/pages/TaskDetailPage.vue"), meta: { requiresAuth: true } },
  { path: "/my-tasks", component: () => import("@/pages/MyTasksPage.vue"), meta: { requiresAuth: true } },
  { path: "/wallet", component: () => import("@/pages/WalletPage.vue"), meta: { requiresAuth: true } },
  { path: "/profile", component: () => import("@/pages/ProfilePage.vue"), meta: { requiresAuth: true } },
  { path: "/notifications", component: () => import("@/pages/NotificationsPage.vue"), meta: { requiresAuth: true } },
  { path: "/chat", component: () => import("@/pages/ChatPage.vue"), meta: { requiresAuth: true } },
  {
    path: "/map",
    component: () => import("@/pages/CampusMapPage.vue"),
    meta: { layout: "map", requiresAuth: true },
  },
  { path: "/admin", component: () => import("@/pages/AdminDashboardPage.vue"), meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

/**
 * 路由守卫：检查认证状态
 */
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  // 如果不需要认证，直接通过
  if (to.meta.requiresAuth === false) {
    next();
    return;
  }

  // 检查是否已认证
  if (authStore.isAuthenticated) {
    next();
    return;
  }

  // 检查是否有令牌（但未初始化用户信息）
  if (authStore.accessToken && !authStore.currentUser) {
    try {
      await authStore.fetchCurrentUser();
      next();
      return;
    } catch (err) {
      // 令牌已过期或无效，清空并重定向到登录
      authStore.clearTokens();
    }
  }

  // 未认证且路由需要认证，重定向到登录
  if (to.meta.requiresAuth !== false) {
    next(`/login?redirect=${to.path}`);
    return;
  }

  next();
});

export default router;

