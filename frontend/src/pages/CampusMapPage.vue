<template>
  <div class="map-page">
    <header class="map-topbar">
      <RouterLink to="/tasks" class="brand">
        <span class="brand-mark"><span></span><span></span><span></span></span>
        <span><strong>CampusMast</strong><small>北邮校园互助平台</small></span>
      </RouterLink>

      <nav>
        <RouterLink to="/tasks">首页</RouterLink>
        <RouterLink to="/tasks">任务大厅</RouterLink>
        <RouterLink to="/tasks/new">发布任务</RouterLink>
        <RouterLink to="/map" class="active">地图</RouterLink>
        <RouterLink to="/notifications" class="badge-link">消息<b>3</b></RouterLink>
        <RouterLink to="/my-tasks">我的⌄</RouterLink>
      </nav>

      <div class="top-actions">
        <label class="search"><input type="search" placeholder="搜索任务、楼宇或关键词" /><span>⌕</span></label>
        <div class="user-chip">
          <span class="avatar">{{ userInitial }}</span>
          <span><strong>你好，{{ authStore.currentUser?.nickname || "同学" }}</strong><small>信用分 {{ authStore.currentUser?.overallCreditScore ?? 828 }}</small></span>
          <i>⌄</i>
        </div>
      </div>
    </header>

    <main class="map-shell">
      <aside class="left-panel">
        <div class="tabs">
          <button :class="{ active: activeTab === 'tasks' }" @click="activeTab = 'tasks'">附近任务</button>
          <button :class="{ active: activeTab === 'buildings' }" @click="activeTab = 'buildings'">楼宇列表</button>
        </div>

        <div class="filter-row">
          <select v-model="buildingFilter">
            <option value="">全部楼宇</option>
            <option v-for="building in mapStore.buildings" :key="building.code" :value="building.code">{{ building.name }}</option>
          </select>
          <select :value="mapStore.activeFilter" @change="changeCategory(($event.target as HTMLSelectElement).value)">
            <option value="all">全部分类</option>
            <option value="package">代取快递</option>
            <option value="food">代买餐食</option>
            <option value="move">搬运重物</option>
            <option value="other">其他</option>
          </select>
          <select disabled>
            <option>3km内</option>
          </select>
        </div>

        <template v-if="activeTab === 'tasks'">
          <p class="panel-hint">当前位置附近 · {{ visiblePanelPins.length }} 个任务</p>
          <div v-if="mapStore.tasksLoading" class="panel-state">正在加载地图任务...</div>
          <div v-else-if="mapStore.tasksError" class="panel-state error">{{ mapStore.tasksError }}</div>
          <div v-else class="nearby-list">
            <article
              v-for="pin in visiblePanelPins"
              :key="pin.id"
              class="nearby-card"
              :class="{ selected: mapStore.activeTaskId === pin.id }"
              @click="mapStore.showTask(pin.id)"
            >
              <div class="pin-icon" :class="`cat-${pin.category}`">{{ categoryIcon(pin.category) }}</div>
              <div class="nearby-main">
                <h3>{{ pin.title }}</h3>
                <span class="task-tag" :class="`tag-${pin.category}`">{{ categoryLabel(pin.category) }}</span>
                <footer>
                  <span class="mini-avatar">{{ pin.requesterName.charAt(0) }}</span>
                  <strong>{{ pin.requesterName }}</strong>
                  <small>信用分 {{ pin.requesterCreditScore }}</small>
                </footer>
              </div>
              <div class="nearby-side">
                <strong>{{ pin.reward.replace("楼", "¥") }}</strong>
                <small>{{ distanceText(pin.distanceKm) }}</small>
                <em>{{ pin.timeLeft }}</em>
              </div>
            </article>
            <RouterLink class="view-all" to="/tasks">查看全部 {{ visiblePanelPins.length }} 个任务 ›</RouterLink>
          </div>
        </template>

        <template v-else>
          <p class="panel-hint">北邮校内常用楼宇</p>
          <div class="building-list">
            <button v-for="building in mapStore.buildings" :key="building.code" @click="mapStore.openBuilding(building.code)">
              <span>⌂</span>
              <strong>{{ building.name }}</strong>
              <small>{{ building.campusZone }}</small>
            </button>
          </div>
        </template>
      </aside>

      <section class="map-board">
        <MapContainer>
          <TaskBeaconLayer />
          <PickerLayer />
        </MapContainer>
      </section>

      <aside class="right-stack">
        <section class="float-card">
          <header><h2>我的常用楼宇</h2><button>管理</button></header>
          <ul class="building-shortcuts">
            <li v-for="building in commonBuildings" :key="building.code">
              <span>⌂</span>
              <strong>{{ building.name }}</strong>
              <small>{{ buildingDistance(building.code) }}</small>
            </li>
          </ul>
        </section>

        <section class="float-card">
          <h2>当前位置附近任务</h2>
          <ul class="category-stats">
            <li><span class="dot all"></span><strong>全部任务</strong><small>{{ mapStore.visiblePins.length }}</small></li>
            <li v-for="stat in categoryStats" :key="stat.key">
              <span class="dot" :style="{ background: stat.color }"></span>
              <strong>{{ stat.label }}</strong>
              <small>{{ stat.count }}</small>
            </li>
          </ul>
        </section>

        <section class="float-card help-card">
          <h2>地图说明</h2>
          <p><span>⌖</span> 点击图标查看任务详情</p>
          <p><span>↕</span> 拖动地图可移动视角</p>
          <p><span>＋</span> 滑动滚轮可缩放地图</p>
          <p><span class="blue-dot"></span> 蓝色范围为步行 5 分钟范围</p>
        </section>
      </aside>

      <Transition name="picker-slide">
        <div v-if="mapStore.pickerMode" class="picker-banner">
          <div>
            <strong>请在地图上点击选择任务地点</strong>
            <span v-if="mapStore.pickedLat">已选：{{ mapStore.pickedLabel }}</span>
          </div>
          <button :disabled="!mapStore.pickedLat" @click="confirmPick">确认选择</button>
          <button @click="cancelPick">取消</button>
        </div>
      </Transition>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import MapContainer from "@/components/map/MapContainer.vue";
import TaskBeaconLayer from "@/components/map/TaskBeaconLayer.vue";
import PickerLayer from "@/components/map/PickerLayer.vue";
import { useAuthStore } from "@/stores/auth";
import { useMapStore, type MapTaskPin } from "@/stores/map";
import type { CategoryType } from "@/types/map";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const mapStore = useMapStore();

const activeTab = ref<"tasks" | "buildings">("tasks");
const buildingFilter = ref("");

const labels: Record<CategoryType, string> = {
  package: "代取快递",
  food: "代买餐食",
  move: "搬运重物",
  other: "其他",
};

const icons: Record<CategoryType, string> = {
  package: "▣",
  food: "▤",
  move: "⇄",
  other: "✦",
};

const colors: Record<CategoryType, string> = {
  package: "#4d83c8",
  food: "#f1892d",
  move: "#52b478",
  other: "#8b75d7",
};

const userInitial = computed(() => authStore.currentUser?.nickname?.charAt(0) || "同");
const visiblePanelPins = computed(() => {
  const pins = mapStore.pinsWithDistance as Array<MapTaskPin & { distanceKm: number | null }>;
  if (!buildingFilter.value) return pins;
  return pins.filter((pin) => pin.buildingCode === buildingFilter.value);
});

const commonBuildings = computed(() => mapStore.buildings.slice(0, 4));
const categoryStats = computed(() =>
  (Object.keys(labels) as CategoryType[]).map((key) => ({
    key,
    label: labels[key],
    color: colors[key],
    count: mapStore.visiblePins.filter((pin) => pin.category === key).length,
  })),
);

function categoryLabel(category: CategoryType) {
  return labels[category];
}

function categoryIcon(category: CategoryType) {
  return icons[category];
}

function distanceText(distanceKm: number | null) {
  return distanceKm == null ? "校内" : `${distanceKm.toFixed(2)}km`;
}

function buildingDistance(code: string) {
  const building = mapStore.buildings.find((item) => item.code === code);
  if (!building || !mapStore.userLocation) return "校内";
  const dLat = ((building.latitude - mapStore.userLocation.lat) * Math.PI) / 180;
  const dLng = ((building.longitude - mapStore.userLocation.lng) * Math.PI) / 180;
  const lat1 = (mapStore.userLocation.lat * Math.PI) / 180;
  const lat2 = (building.latitude * Math.PI) / 180;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return `${(6371 * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h))).toFixed(2)}km`;
}

function changeCategory(value: string) {
  mapStore.setFilter(value);
}

function onKeydown(e: KeyboardEvent) {
  if (mapStore.pickerMode && e.key === "Escape") {
    cancelPick();
    return;
  }
  if (e.key === "Escape") mapStore.clearAll();
}

function confirmPick() {
  if (!mapStore.pickedLat || !mapStore.pickedLng) return;
  const lat = mapStore.pickedLat;
  const lng = mapStore.pickedLng;
  mapStore.leavePickerMode();
  router.replace({ path: "/tasks/new", query: { lat: String(lat), lng: String(lng) } });
}

function cancelPick() {
  mapStore.leavePickerMode();
  router.back();
}

onMounted(() => {
  document.addEventListener("keydown", onKeydown);
  mapStore.fetchMapData();
  if (route.query.mode === "pick-building") mapStore.enterPickerMode();
});

onUnmounted(() => {
  document.removeEventListener("keydown", onKeydown);
  mapStore.leavePickerMode();
});
</script>

<style scoped>
.map-page {
  position: fixed;
  inset: 0;
  display: grid;
  grid-template-rows: 98px 1fr;
  background: #fbfaf7;
  color: #252723;
  font-family: "Inter", "Noto Sans SC", "Microsoft YaHei", sans-serif;
}

.map-topbar {
  display: grid;
  grid-template-columns: 270px 1fr 560px;
  align-items: center;
  gap: 24px;
  padding: 0 60px;
  background: rgba(251, 250, 247, 0.92);
  border-bottom: 1px solid rgba(74, 84, 64, 0.08);
  backdrop-filter: blur(18px);
  z-index: 20;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: inherit;
  text-decoration: none;
}

.brand > span:last-child {
  display: grid;
  line-height: 1.15;
}

.brand strong {
  font-size: 20px;
  font-weight: 900;
}

.brand small {
  margin-top: 3px;
  color: #8c887f;
  font-size: 13px;
}

.brand-mark {
  position: relative;
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: linear-gradient(145deg, #6f835f, #536b48);
}

.brand-mark span {
  position: absolute;
  width: 18px;
  height: 10px;
  border: 2px solid #fff;
  border-top: 0;
  border-radius: 2px;
  transform: rotate(30deg) skewX(-18deg);
}

.brand-mark span:nth-child(1) { margin-top: -9px; opacity: 0.9; }
.brand-mark span:nth-child(2) { opacity: 0.82; }
.brand-mark span:nth-child(3) { margin-top: 9px; opacity: 0.74; }

.map-topbar nav {
  display: flex;
  justify-content: center;
  gap: 34px;
}

.map-topbar nav a {
  position: relative;
  padding: 13px 4px;
  color: #22241f;
  text-decoration: none;
  font-weight: 800;
}

.map-topbar nav a.active::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: 0;
  width: 32px;
  height: 3px;
  border-radius: 999px;
  background: #6f835f;
  transform: translateX(-50%);
}

.badge-link b,
.bell b {
  position: absolute;
  min-width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: #ef4e5b;
  color: #fff;
  font-size: 11px;
}

.badge-link b {
  top: 1px;
  right: -16px;
}

.top-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 18px;
}

.search {
  width: 292px;
  height: 44px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  border: 1px solid #eceae4;
  border-radius: 10px;
  background: #fff;
}

.search input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  font: inherit;
  font-size: 13px;
}

.bell {
  position: relative;
  color: #33342f;
  text-decoration: none;
  font-size: 22px;
}

.bell b {
  top: -8px;
  right: -10px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #e9ded1;
  color: #596d4b;
  font-weight: 900;
}

.user-chip span:nth-child(2) {
  display: grid;
  line-height: 1.15;
}

.user-chip strong {
  font-size: 13px;
}

.user-chip small {
  margin-top: 4px;
  color: #8c887f;
  font-size: 12px;
}

.map-shell {
  position: relative;
  min-height: 0;
  padding: 0 60px 46px;
  display: grid;
  grid-template-columns: 430px minmax(0, 1fr);
  gap: 0;
}

.left-panel {
  z-index: 5;
  margin-top: 0;
  padding: 24px;
  border: 1px solid #e8e5dc;
  border-right: 0;
  border-radius: 18px 0 0 18px;
  background: rgba(255, 253, 250, 0.95);
  box-shadow: 0 18px 44px rgba(65, 57, 46, 0.08);
  overflow: auto;
}

.tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  margin-bottom: 18px;
  padding: 4px;
  border-radius: 10px;
  background: #f2f2ee;
}

.tabs button {
  height: 46px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: #8a8a82;
  cursor: pointer;
  font: inherit;
  font-weight: 900;
}

.tabs button.active {
  background: #fffdfa;
  color: #6f835f;
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.filter-row select {
  height: 38px;
  min-width: 0;
  border: 1px solid #e3dfd6;
  border-radius: 8px;
  background: #fff;
  color: #41433e;
  font: inherit;
  font-size: 12px;
}

.filter-row select:disabled {
  color: #9b9d97;
}

.panel-hint {
  margin: 22px 0 14px;
  color: #70825f;
  font-size: 14px;
  font-weight: 800;
}

.panel-state {
  display: grid;
  place-items: center;
  min-height: 220px;
  color: #85877f;
}

.panel-state.error {
  color: #b24a3a;
}

.nearby-list {
  display: grid;
  gap: 10px;
}

.nearby-card {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr) 72px;
  gap: 12px;
  align-items: center;
  min-height: 104px;
  padding: 13px;
  border: 1px solid #ece8df;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
}

.nearby-card:hover,
.nearby-card.selected {
  border-color: #b8c8ae;
  box-shadow: 0 10px 24px rgba(91, 111, 76, 0.12);
}

.pin-icon {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  font-size: 24px;
  font-weight: 900;
}

.cat-package { background: #edf4fb; color: #4d7db9; }
.cat-food { background: #fbf0df; color: #c77923; }
.cat-move { background: #eff5ec; color: #6d835f; }
.cat-other { background: #f0edfb; color: #8171c7; }

.nearby-main {
  min-width: 0;
}

.nearby-main h3 {
  margin: 0 0 7px;
  overflow: hidden;
  color: #191b17;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 15px;
  font-weight: 900;
}

.task-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 800;
}

.tag-package { background: #e8f1fb; color: #4778b4; }
.tag-food { background: #faecd8; color: #c97a25; }
.tag-move { background: #e8f0e3; color: #6d835f; }
.tag-other { background: #ebe7f8; color: #7b6cc4; }

.nearby-main footer {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 11px;
  color: #8a8c85;
  font-size: 12px;
}

.nearby-main .mini-avatar {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #e5d9cb;
  color: #596d4b;
  font-weight: 900;
}

.nearby-main footer strong {
  color: #2d2f2a;
}

.nearby-side {
  display: grid;
  justify-items: end;
  gap: 7px;
}

.nearby-side strong {
  color: #6f835f;
  font-size: 19px;
}

.nearby-side small,
.nearby-side em {
  color: #83857e;
  font-size: 12px;
  font-style: normal;
}

.view-all {
  padding: 8px;
  color: #6f835f;
  text-align: center;
  text-decoration: none;
  font-weight: 900;
}

.building-list {
  display: grid;
  gap: 10px;
}

.building-list button {
  display: grid;
  grid-template-columns: 42px 1fr;
  gap: 10px;
  align-items: center;
  padding: 12px;
  border: 1px solid #ece8df;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  text-align: left;
}

.building-list span {
  grid-row: span 2;
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #eef4ea;
  color: #6f835f;
}

.building-list small {
  color: #8b8d86;
}

.map-board {
  min-width: 0;
  margin-bottom: 0;
  overflow: hidden;
  border: 1px solid #e8e5dc;
  border-radius: 0 18px 18px 0;
  box-shadow: 0 18px 44px rgba(65, 57, 46, 0.08);
}

.right-stack {
  position: absolute;
  top: 54px;
  right: 78px;
  z-index: 6;
  width: 270px;
  display: grid;
  gap: 14px;
}

.float-card {
  padding: 20px;
  border: 1px solid #ece8df;
  border-radius: 14px;
  background: rgba(255, 253, 250, 0.95);
  box-shadow: 0 18px 38px rgba(65, 57, 46, 0.12);
  backdrop-filter: blur(12px);
}

.float-card header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.float-card h2 {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 900;
}

.float-card header h2 {
  margin-bottom: 0;
}

.float-card button {
  border: 0;
  background: transparent;
  color: #6f835f;
  cursor: pointer;
  font-weight: 800;
}

.building-shortcuts,
.category-stats {
  display: grid;
  gap: 14px;
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
}

.building-shortcuts li,
.category-stats li {
  display: grid;
  grid-template-columns: 32px 1fr auto;
  align-items: center;
  gap: 10px;
}

.building-shortcuts span {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #eef4ea;
  color: #6f835f;
}

.building-shortcuts strong,
.category-stats strong {
  font-size: 13px;
}

.building-shortcuts small,
.category-stats small {
  color: #8b8d86;
  font-size: 12px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

.dot.all {
  background: #6f835f;
}

.help-card {
  display: grid;
  gap: 10px;
}

.help-card p {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  color: #74766f;
  font-size: 13px;
}

.help-card span {
  width: 22px;
  color: #6f835f;
}

.blue-dot {
  width: 14px !important;
  height: 14px;
  border-radius: 50%;
  background: #d8e7fb;
}

.picker-banner {
  position: absolute;
  left: 50%;
  bottom: 24px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid #e8e5dc;
  border-radius: 14px;
  background: #fffdfa;
  box-shadow: 0 18px 44px rgba(65, 57, 46, 0.14);
  transform: translateX(-50%);
}

.picker-banner div {
  display: grid;
}

.picker-banner span {
  color: #6f835f;
  font-size: 12px;
}

.picker-banner button {
  height: 36px;
  border: 0;
  border-radius: 8px;
  background: #6f835f;
  color: #fff;
  cursor: pointer;
  font-weight: 900;
}

.picker-banner button:last-child {
  background: #f0efeb;
  color: #4e514a;
}

.picker-banner button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 1180px) {
  .map-topbar {
    grid-template-columns: 230px 1fr;
    padding: 0 24px;
  }

  .top-actions {
    display: none;
  }

  .map-shell {
    grid-template-columns: 360px minmax(0, 1fr);
    padding: 0 24px 28px;
  }

  .right-stack {
    display: none;
  }
}
</style>
