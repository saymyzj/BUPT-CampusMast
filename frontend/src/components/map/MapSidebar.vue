<template>
  <aside class="map-sidebar" :class="{ collapsed }">
    <div class="sidebar-brand">
      <div class="brand-mark">CM</div>
      <div v-if="!collapsed" class="brand-copy">
        <strong>CampusMast</strong>
        <span>校园互助 · 让帮助更简单</span>
      </div>
    </div>

    <nav class="sidebar-nav">
      <button
        v-for="item in navItems"
        :key="item.id"
        class="nav-item"
        :class="{ active: activeNav === item.id }"
        :style="activeNav === item.id ? { '--active-color': item.color } : {}"
        @click="navigate(item.route)"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
        <span v-if="item.badge && !collapsed" class="nav-badge">{{ item.badge }}</span>
      </button>
    </nav>

    <div v-if="!collapsed" class="sidebar-map-info">
      <section class="sidebar-section">
        <div class="section-title">数据概览</div>
        <div class="overview-grid">
          <div v-for="s in mapStore.overviewStats" :key="s.label" class="ov-cell">
            <span class="ov-icon" :style="{ background: s.color }">{{ s.icon }}</span>
            <span class="ov-label">{{ s.label }}</span>
            <span class="ov-value">{{ s.value }}</span>
          </div>
        </div>
      </section>

      <section class="sidebar-section">
        <div class="section-title">图例说明</div>
        <div class="legend-list">
          <div v-for="item in legendItems" :key="item.label" class="legend-item">
            <span class="legend-dot" :style="{ background: item.color }">{{ item.icon }}</span>
            <span class="legend-label">{{ item.label }}</span>
          </div>
        </div>
      </section>
    </div>

    <div class="sidebar-spacer"></div>

    <button v-if="!collapsed" class="publish-btn" @click="router.push('/tasks/new')">
      <span class="publish-main">＋ 发布任务</span>
      <span class="publish-sub">发布跑腿 / 代取 / 拼车等</span>
    </button>
    <button v-else class="publish-btn-collapsed" @click="router.push('/tasks/new')">＋</button>
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useMapStore } from "@/stores/map";
import { CATEGORY_COLORS } from "@/types/map";

defineProps<{ collapsed: boolean }>();

const route = useRoute();
const router = useRouter();
const mapStore = useMapStore();

const navItems = [
  { id: "map", icon: "📍", label: "地图", route: "/map", color: "#6C5CE7" },
  { id: "tasks", icon: "▤", label: "任务大厅", route: "/tasks", color: "gray" },
  { id: "my-tasks", icon: "☑", label: "我的任务", route: "/my-tasks", color: "gray" },
  { id: "notifications", icon: "♢", label: "消息中心", route: "/notifications", color: "gray", badge: 0 },
  { id: "wallet", icon: "▣", label: "积分钱包", route: "/wallet", color: "gray" },
];

const legendItems = [
  { label: "代取快递", icon: "📦", color: CATEGORY_COLORS.package },
  { label: "代买餐食", icon: "🍱", color: CATEGORY_COLORS.food },
  { label: "搬运重物", icon: "📦", color: CATEGORY_COLORS.move },
  { label: "其他", icon: "🔧", color: CATEGORY_COLORS.other },
];

const activeNav = computed(() => {
  const path = route.path;
  for (const item of navItems) {
    if (path === item.route) return item.id;
    if (item.route !== "/map" && item.route !== "/tasks" && path.startsWith(item.route)) return item.id;
  }
  return "tasks";
});

function navigate(to: string) {
  router.push(to);
}
</script>

<style scoped>
.map-sidebar {
  width: 263px;
  min-width: 263px;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-right: 1px solid #eef0f5;
  box-shadow: 10px 0 34px rgba(31, 36, 48, 0.04);
  transition: width 260ms ease, min-width 260ms ease;
  overflow: hidden;
  z-index: 40;
}

.map-sidebar.collapsed {
  width: 68px;
  min-width: 68px;
}

.sidebar-brand {
  height: 76px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
}

.brand-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 13px;
  color: #fff;
  background: #111827;
  font-family: "Fredoka", "Noto Sans SC", sans-serif;
  font-weight: 900;
  font-size: 14px;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.16);
}

.brand-copy strong {
  display: block;
  color: #171b27;
  font-size: 20px;
  line-height: 1.1;
  font-weight: 900;
}

.brand-copy span {
  display: block;
  margin-top: 4px;
  color: #9ca3af;
  font-size: 12px;
  white-space: nowrap;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px 14px 8px;
}

.nav-item {
  height: 48px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 14px;
  border: none;
  border-radius: 0;
  background: transparent;
  cursor: pointer;
  color: #686f7e;
  font-family: inherit;
  font-size: 15px;
  font-weight: 700;
  text-align: left;
  white-space: nowrap;
  transition: background 160ms ease, color 160ms ease, box-shadow 160ms ease;
}

.nav-item:hover {
  color: #6c5ce7;
  background: #f6f3ff;
}

.nav-item.active {
  color: #6c5ce7;
  background: linear-gradient(90deg, rgba(108, 92, 231, 0.14), rgba(108, 92, 231, 0.04));
  box-shadow: inset 3px 0 0 var(--active-color, #6c5ce7);
}

.nav-icon {
  width: 24px;
  flex-shrink: 0;
  text-align: center;
  font-size: 20px;
  line-height: 1;
}

.nav-label {
  flex: 1;
}

.nav-badge {
  min-width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  padding: 0 5px;
  border-radius: 9px;
  color: #fff;
  background: #ff4757;
  font-size: 10px;
  font-weight: 900;
}

.sidebar-spacer {
  flex: 1;
}

.sidebar-map-info {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 12px 18px 0;
}

.sidebar-section {
  padding-top: 14px;
  border-top: 1px solid #eef0f5;
}

.section-title {
  margin-bottom: 12px;
  color: #232937;
  font-size: 13px;
  font-weight: 900;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 8px;
}

.ov-cell {
  min-width: 0;
  display: grid;
  grid-template-columns: 22px 1fr;
  column-gap: 7px;
  align-items: center;
}

.ov-icon,
.legend-dot {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  color: #fff;
  font-size: 10px;
  font-weight: 900;
}

.ov-icon {
  width: 22px;
  height: 22px;
  grid-row: span 2;
  border-radius: 8px;
}

.ov-label {
  color: #7d8493;
  font-size: 11px;
  line-height: 1.1;
}

.ov-value {
  color: #202633;
  font-size: 17px;
  font-weight: 900;
  line-height: 1.1;
}

.legend-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 7px;
  color: #5c6474;
  font-size: 12px;
  font-weight: 700;
}

.legend-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
}

.legend-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.publish-btn {
  height: 72px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  margin: 0 18px 24px;
  border: none;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, #8657ff, #596cff);
  box-shadow: 0 18px 34px rgba(108, 92, 231, 0.28);
  cursor: pointer;
  font-family: inherit;
}

.publish-main {
  font-size: 18px;
  font-weight: 900;
}

.publish-sub {
  font-size: 12px;
  opacity: 0.86;
}

.publish-btn-collapsed {
  width: 46px;
  height: 46px;
  margin: 14px auto 24px;
  border: none;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(135deg, #8657ff, #596cff);
  cursor: pointer;
  font-size: 24px;
  font-weight: 700;
}
</style>
