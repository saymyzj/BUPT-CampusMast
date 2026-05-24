<!-- @deprecated Replaced by MapSidebar.vue + MapFloatingPanel.vue + BottomTaskBar.vue -->
<template>
  <div class="hud-scroll">
    <div class="hud">
      <!-- Brand -->
      <div class="brand">
        <div class="brand-mark">CM</div>
        <div class="brand-meta">
          <strong>CampusMast</strong>
          <span>北邮西土城 · 任务地图</span>
        </div>
        <button class="back-link" @click="router.push('/tasks')">← 返回</button>
      </div>

      <div class="divider"></div>

      <!-- Category filters -->
      <div class="filters">
        <button class="filter-btn" :class="{ active: mapStore.activeFilter === 'all' }" @click="mapStore.setFilter('all')">全部</button>
        <button class="filter-btn" :class="{ active: mapStore.activeFilter === 'package' }" @click="mapStore.setFilter('package')">📦 快递</button>
        <button class="filter-btn" :class="{ active: mapStore.activeFilter === 'food' }" @click="mapStore.setFilter('food')">🍜 餐食</button>
        <button class="filter-btn" :class="{ active: mapStore.activeFilter === 'move' }" @click="mapStore.setFilter('move')">📦 搬运</button>
      </div>

      <div class="divider"></div>

      <!-- Loading / Error -->
      <div v-if="mapStore.tasksLoading" class="hud-note">加载任务中...</div>
      <div v-else-if="mapStore.tasksError" class="hud-note hud-err">{{ mapStore.tasksError }}</div>

      <span class="stat-line">{{ mapStore.visiblePins.length }} 个任务</span>
      <span class="stat-line gold">¥{{ rewardPool }} 赏金池</span>

      <div class="divider"></div>

      <!-- Task Card List -->
      <div class="task-cards">
        <div
          v-for="pin in mapStore.visiblePins"
          :key="pin.id"
          class="task-cards-item"
          :class="{ focused: mapStore.focusTaskId === pin.id }"
          @click="focusTask(pin)"
          @mouseenter="mapStore.setFocus(pin.id)"
          @mouseleave="mapStore.setFocus(null)"
        >
          <div class="tci-top">
            <span class="tci-tag" :class="`tci-tag-${pin.category}`">{{ pin.label }}</span>
            <span class="tci-reward" :style="{ color: CATEGORY_COLORS[pin.category] }">{{ pin.reward }}</span>
          </div>
          <div class="tci-title">{{ pin.title }}</div>
          <div class="tci-meta">{{ pin.timeLeft }}</div>
        </div>
        <div v-if="mapStore.visiblePins.length === 0 && !mapStore.tasksLoading" class="hud-note">
          暂无任务
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useMapStore } from "@/stores/map";
import type { MapTaskPin } from "@/stores/map";
import { CATEGORY_COLORS } from "@/types/map";

const router = useRouter();
const mapStore = useMapStore();

const rewardPool = computed(() => {
  const total = mapStore.visiblePins.reduce((sum, p) => {
    const v = parseFloat(p.reward.replace("¥", ""));
    return sum + (isNaN(v) ? 0 : v);
  }, 0);
  return total % 1 === 0 ? total.toFixed(0) : total.toFixed(2);
});

function focusTask(pin: MapTaskPin) {
  mapStore.setFocus(pin.id);
  mapStore.showTask(pin.id);
}
</script>

<style scoped>
.hud-scroll {
  overflow-y: auto;
  flex: 1;
}

.hud {
  padding: 22px 20px 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  width: 38px; height: 38px;
  display: grid; place-items: center;
  border-radius: 11px;
  background: #1f2230; color: #f0c94a;
  font-family: "Fredoka", sans-serif; font-weight: 700; font-size: 15px;
  letter-spacing: -0.03em; flex-shrink: 0;
}

.brand-meta strong {
  display: block;
  font-family: "Fredoka", sans-serif;
  font-size: 17px; font-weight: 700; color: #1f2230;
  letter-spacing: -0.02em;
}

.brand-meta span {
  display: block;
  font-size: 11px; color: #919bab; font-weight: 500; margin-top: 2px;
}

.back-link {
  margin-left: auto; padding: 6px 12px;
  border: 1px solid rgba(31, 42, 58, 0.1); border-radius: 8px;
  background: transparent; color: #7b8698;
  font-size: 12px; font-weight: 600; cursor: pointer;
  transition: all 0.2s; white-space: nowrap;
  font-family: "Noto Sans SC", sans-serif;
}
.back-link:hover {
  border-color: #1f2230; color: #1f2230;
  background: rgba(31, 34, 48, 0.04);
}

.divider {
  height: 1px; background: rgba(31, 42, 58, 0.06); margin: 16px 0;
}

.filters { display: flex; gap: 6px; }

.filter-btn {
  flex: 1;
  border: 1.5px solid rgba(31, 42, 58, 0.08); background: transparent;
  color: #7b8698; padding: 9px 6px; border-radius: 12px; cursor: pointer;
  font-family: "Fredoka", "Noto Sans SC", sans-serif;
  font-size: 12px; font-weight: 600;
  transition: all 220ms cubic-bezier(0.22, 1, 0.36, 1); white-space: nowrap;
}
.filter-btn:hover {
  border-color: rgba(31, 42, 58, 0.15); color: #1f2230;
  background: rgba(31, 42, 58, 0.03);
}
.filter-btn.active {
  background: #1f2230; color: #f0c94a; border-color: #1f2230;
  box-shadow: 0 2px 10px rgba(31, 34, 48, 0.18); transform: scale(1.02);
}

.stat-line {
  display: block;
  font-family: "Fredoka", sans-serif; font-size: 18px; font-weight: 700;
  color: #1f2230; letter-spacing: -0.02em;
}
.stat-line.gold { color: #c49a2e; }

.hud-note { padding: 8px 0; font-size: 12px; color: #919bab; text-align: center; }
.hud-err { color: #b24a3a; }

/* ===== Task Cards ===== */
.task-cards {
  display: flex; flex-direction: column; gap: 6px;
}

.task-cards-item {
  padding: 10px 14px;
  border-radius: 14px;
  border: 1.5px solid rgba(31, 42, 58, 0.06);
  background: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s;
}

.task-cards-item:hover,
.task-cards-item.focused {
  border-color: #2556a8;
  background: #edf3fb;
  transform: translateX(-2px);
}

.tci-top {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 6px;
}

.tci-tag {
  font-size: 10px; font-weight: 700; padding: 2px 8px;
  border-radius: 999px;
}

.tci-tag-package { background: #dbeafe; color: #1e40af; }
.tci-tag-food { background: #fef3c7; color: #92400e; }
.tci-tag-move { background: #ede9fe; color: #6b21a8; }
.tci-tag-other { background: #f3f4f6; color: #374151; }

.tci-reward {
  font-family: "Fredoka", sans-serif; font-size: 15px; font-weight: 700;
}

.tci-title {
  font-size: 13px; font-weight: 600; color: #1f2230;
  line-height: 1.35;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}

.tci-meta {
  font-size: 11px; color: #919bab; margin-top: 4px;
}
</style>
