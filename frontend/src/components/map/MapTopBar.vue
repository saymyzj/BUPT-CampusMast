<template>
  <header class="map-topbar">
    <div class="topbar-left">
      <button class="collapse-btn" title="收起侧栏" @click="$emit('toggleSidebar')">‹</button>
      <span class="topbar-title">校园任务地图</span>
    </div>

    <div class="topbar-actions">
      <label class="filter-select-wrap">
        <span class="filter-icon">⌯</span>
        <select class="filter-select" :value="mapStore.activeFilter" @change="onFilterChange">
          <option v-for="option in filterOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>
      <button class="view-btn" title="列表视图" @click="router.push('/tasks')">
        <span class="view-icon">☷</span>
        <span>列表视图</span>
      </button>
      <button class="avatar" title="个人资料" @click="toggleUserMenu">
        {{ authStore.currentUser?.nickname?.charAt(0) || "?" }}
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { useMapStore } from "@/stores/map";
import { useAuthStore } from "@/stores/auth";

defineEmits<{ toggleSidebar: [] }>();

const router = useRouter();
const mapStore = useMapStore();
const authStore = useAuthStore();

const filterOptions = [
  { value: "all", label: "全部任务" },
  { value: "package", label: "代取快递" },
  { value: "food", label: "代买餐食" },
  { value: "move", label: "搬运重物" },
  { value: "other", label: "其他" },
];

function onFilterChange(e: Event) {
  mapStore.setFilter((e.target as HTMLSelectElement).value);
}

function toggleUserMenu() {
  router.push("/profile");
}
</script>

<style scoped>
.map-topbar {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 1px 0 rgba(31, 36, 48, 0.06);
  z-index: 30;
}

.topbar-left,
.topbar-actions {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 12px;
}

.topbar-left {
  flex: 1;
}

.topbar-title {
  overflow: hidden;
  color: #202633;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 18px;
  font-weight: 900;
}

.collapse-btn {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: none;
  border-radius: 10px;
  color: #6d7280;
  background: transparent;
  cursor: pointer;
  font-size: 24px;
  line-height: 1;
}

.collapse-btn:hover {
  color: #6c5ce7;
  background: #f3f0ff;
}

.filter-select-wrap,
.view-btn,
.round-btn,
.avatar {
  border: 1px solid #eceef3;
  background: #fff;
  box-shadow: 0 8px 22px rgba(31, 36, 48, 0.05);
  cursor: pointer;
  font-family: inherit;
}

.filter-select-wrap,
.view-btn {
  height: 40px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 12px;
  padding: 0 14px;
  color: #3a4050;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.filter-select-wrap {
  padding: 0 10px 0 12px;
}

.filter-icon {
  color: #7c4dff;
  font-size: 16px;
  line-height: 1;
}

.filter-select {
  min-width: 108px;
  border: none;
  outline: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  appearance: auto;
}

.view-icon {
  font-size: 18px;
  line-height: 1;
}

.round-btn,
.avatar {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  color: #202633;
  position: relative;
  font-weight: 800;
}

.avatar {
  border-radius: 50%;
  color: #fff;
  border: none;
  background: linear-gradient(145deg, #4a4650, #c8b2a6);
}

.badge {
  position: absolute;
  top: 6px;
  right: 7px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff4757;
  color: transparent;
}

@media (max-width: 760px) {
  .map-topbar {
    height: auto;
    padding: 12px;
    align-items: stretch;
    flex-direction: column;
  }

  .topbar-actions {
    overflow-x: auto;
    padding-bottom: 2px;
  }
}
</style>
