<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar-inner">
        <RouterLink to="/tasks" class="brand">
          <span class="brand-mark"><i></i><i></i><i></i></span>
          <span class="brand-copy">
            <strong>CampusMast</strong>
            <small>北邮校园互助平台</small>
          </span>
        </RouterLink>

        <nav class="nav-links">
          <RouterLink to="/tasks" class="nav-link nav-home">首页</RouterLink>
          <RouterLink to="/tasks/new" class="nav-link">发布任务</RouterLink>
          <RouterLink to="/map" class="nav-link">地图</RouterLink>
          <RouterLink to="/chat" class="nav-link nav-message">
            消息
            <span v-if="messageBadgeCount">{{ messageBadgeText }}</span>
          </RouterLink>
          <RouterLink to="/my-tasks" class="nav-link">我的</RouterLink>
        </nav>

        <div class="top-actions">
          <form class="global-search" role="search" @submit.prevent="runGlobalSearch">
            <input v-model.trim="globalKeyword" type="search" placeholder="搜索任务关键词" />
            <button type="submit" aria-label="搜索任务关键词"><AppIcon name="search" /></button>
          </form>

          <div v-if="authStore.isAuthenticated" ref="userMenuRef" class="user-menu-wrap">
            <button type="button" class="user-chip" @click.stop="toggleUserMenu">
              <span class="avatar">{{ userInitial }}</span>
              <span class="user-copy">
                <strong>你好，{{ authStore.currentUser?.nickname || "邮仔" }}</strong>
                <small>信用分 {{ authStore.currentUser?.overallCreditScore ?? 828 }}</small>
              </span>
            </button>
            <div v-if="showUserMenu" class="dropdown">
              <RouterLink class="dropdown-item" to="/profile" @click="showUserMenu = false">个人资料</RouterLink>
              <RouterLink class="dropdown-item" to="/wallet" @click="showUserMenu = false">钱包</RouterLink>
              <RouterLink class="dropdown-item" to="/admin" @click="showUserMenu = false">运营后台</RouterLink>
              <button type="button" class="dropdown-item danger" @click="handleLogout">退出登录</button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="shell-main">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useNotificationStore } from "@/stores/notification";
import AppIcon from "@/components/ui/AppIcon.vue";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const showUserMenu = ref(false);
const userMenuRef = ref<HTMLElement | null>(null);
const globalKeyword = ref("");

const userInitial = computed(() => authStore.currentUser?.nickname?.charAt(0) || "邮");
const messageBadgeCount = computed(() => notificationStore.totalUnreadCount);
const messageBadgeText = computed(() => (messageBadgeCount.value > 99 ? "99+" : String(messageBadgeCount.value)));

function routeKeyword() {
  return typeof route.query.keyword === "string" ? route.query.keyword : "";
}

function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value;
}

function handleDocumentClick(e: MouseEvent) {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target as Node)) showUserMenu.value = false;
}

async function handleLogout() {
  showUserMenu.value = false;
  authStore.logout();
  await router.push({ path: "/login", query: { reason: "logout" } });
}

async function runGlobalSearch() {
  const keyword = globalKeyword.value.trim();
  await router.push({ path: "/tasks", query: keyword ? { keyword } : {} });
}

watch(
  () => route.query.keyword,
  () => {
    globalKeyword.value = routeKeyword();
  },
);

watch(
  () => route.fullPath,
  () => {
    if (authStore.isAuthenticated) void notificationStore.refreshUnreadCounts();
  },
);

onMounted(() => {
  globalKeyword.value = routeKeyword();
  document.addEventListener("click", handleDocumentClick);
  if (authStore.isAuthenticated) void notificationStore.refreshUnreadCounts();
});
onBeforeUnmount(() => document.removeEventListener("click", handleDocumentClick));
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: #fbfaf7;
  color: #1f211d;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 62px;
  background: rgba(251, 250, 247, 0.94);
  backdrop-filter: blur(14px);
}

.topbar::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 1px;
  background: rgba(80, 80, 72, 0.07);
  pointer-events: none;
}

.topbar-inner {
  width: min(1440px, 100%);
  height: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  padding: 0 51px;
}

.brand {
  width: 240px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: inherit;
  text-decoration: none;
}

.brand-mark {
  position: relative;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  border-radius: 9px;
  background: linear-gradient(145deg, #728766, #536b49);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.brand-mark i {
  position: absolute;
  left: 9px;
  width: 15px;
  height: 8px;
  border: 2px solid #fff;
  border-top: 0;
  border-radius: 2px;
  transform: rotate(30deg) skewX(-18deg);
}

.brand-mark i:nth-child(1) { top: 8px; opacity: 0.92; }
.brand-mark i:nth-child(2) { top: 13px; opacity: 0.84; }
.brand-mark i:nth-child(3) { top: 18px; opacity: 0.76; }

.brand-copy {
  display: grid;
  line-height: 1.12;
}

.brand-copy strong {
  font-size: 17px;
  font-weight: 900;
}

.brand-copy small {
  margin-top: 3px;
  color: #858781;
  font-size: 11px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 28px;
  margin-left: 62px;
}

.nav-link {
  position: relative;
  height: 34px;
  min-width: 48px;
  display: grid;
  place-items: center;
  padding: 0 8px;
  border-radius: 11px;
  color: #1f211d;
  text-decoration: none;
  font-size: 14px;
  font-weight: 800;
  white-space: nowrap;
  transition: color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}

.nav-link:hover {
  color: #627653;
  transform: translateY(-1px);
}

.nav-link.router-link-active::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: -6px;
  width: 30px;
  height: 3px;
  border-radius: 999px;
  background: #6f835f;
  transform: translateX(-50%);
}

.nav-message span {
  position: absolute;
  width: 17px;
  height: 17px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #ef4e5b;
  color: #fff;
  font-size: 10px;
  font-weight: 900;
}

.nav-message span {
  right: -8px;
  top: -6px;
}

.top-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 20px;
}

.global-search {
  width: 257px;
  height: 34px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 13px;
  border: 1px solid #ece9e2;
  border-radius: 9px;
  background: #fff;
  box-shadow: 0 9px 20px rgba(60, 54, 45, 0.04);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.global-search:focus-within {
  border-color: rgba(58, 120, 214, 0.38);
  box-shadow: 0 0 0 4px rgba(58, 120, 214, 0.08), 0 10px 24px rgba(60, 54, 45, 0.05);
}

.global-search input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  color: #2c2d29;
  font-size: 12px;
}

.global-search button {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #8a8d86;
  cursor: pointer;
  font-size: 17px;
  line-height: 1;
  transition: color 0.18s ease, transform 0.18s ease;
}

.global-search button:hover {
  color: #3a78d6;
  transform: scale(1.08);
}

.user-menu-wrap {
  position: relative;
}

.user-chip {
  height: 36px;
  display: flex;
  align-items: center;
  gap: 9px;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  transition: transform 0.18s ease;
}

.user-chip:hover {
  transform: translateY(-1px);
}

.avatar {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: linear-gradient(135deg, #e5c5a7, #8aa078);
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  overflow: hidden;
}

.user-copy {
  width: 93px;
  display: grid;
  line-height: 1.12;
  text-align: left;
}

.user-copy strong {
  font-size: 12px;
  font-weight: 900;
}

.user-copy small {
  margin-top: 4px;
  color: #858781;
  font-size: 11px;
}

.dropdown {
  position: absolute;
  right: 0;
  top: 42px;
  width: 178px;
  padding: 8px;
  border: 1px solid #ebe8df;
  border-radius: 13px;
  background: #fff;
  box-shadow: 0 18px 40px rgba(49, 44, 35, 0.12);
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 10px 12px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: #2a2b27;
  text-align: left;
  text-decoration: none;
  cursor: pointer;
  font: inherit;
  font-size: 14px;
}

.dropdown-item:hover {
  background: #f4f4ef;
}

.dropdown-item.danger {
  color: #b24a3a;
}

.shell-main {
  min-height: calc(100vh - 62px);
}

@media (max-width: 1180px) {
  .topbar-inner {
    padding: 0 24px;
  }

  .nav-links {
    gap: 14px;
    margin-left: 22px;
  }

  .top-actions {
    display: none;
  }
}
</style>
