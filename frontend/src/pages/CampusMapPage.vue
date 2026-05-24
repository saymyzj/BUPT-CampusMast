<template>
  <div class="map-page">
    <main class="map-shell">
      <aside class="left-panel">
        <div class="panel-toolbar">
          <strong>附近任务</strong>
          <select :value="mapStore.activeFilter" @change="changeCategory(($event.target as HTMLSelectElement).value)">
            <option value="all">全部分类</option>
            <option value="package">代取快递</option>
            <option value="food">代买餐食</option>
            <option value="move">搬运重物</option>
            <option value="other">其他</option>
          </select>
        </div>

        <p class="panel-hint">当前位置附近 · {{ visiblePanelPins.length }} 个任务</p>
        <div class="task-scroll">
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
              <div class="pin-icon" :class="`cat-${pin.category}`">
                <AppIcon :name="categoryIcon(pin.category)" />
              </div>
              <div class="nearby-main">
                <h3>{{ pin.title }}</h3>
                <div class="nearby-meta">
                  <span class="task-tag" :class="`tag-${pin.category}`">{{ categoryLabel(pin.category) }}</span>
                  <span class="location-text"><AppIcon name="location" />{{ locationText(pin) }}</span>
                </div>
              </div>
              <div class="nearby-side">
                <strong>{{ pin.reward }}</strong>
                <em>{{ pin.timeLeft }}</em>
                <footer>
                  <span class="mini-avatar">{{ pin.requesterName.charAt(0) }}</span>
                  <span class="user-text">
                    <b>{{ pin.requesterName }}</b>
                    <small class="credit">信用分 {{ pin.requesterCreditScore }}</small>
                  </span>
                </footer>
              </div>
            </article>
            <RouterLink class="view-all" to="/tasks">查看全部 {{ visiblePanelPins.length }} 个任务 ›</RouterLink>
          </div>
        </div>
      </aside>

      <section class="map-board">
        <MapContainer>
          <TaskBeaconLayer />
          <PickerLayer />
        </MapContainer>
      </section>

      <aside class="right-stack">
        <section class="float-card">
          <h2>当前位置附近任务</h2>
          <ul class="category-stats">
            <li><span class="legend-icon all"><AppIcon name="spark" /></span><strong>全部任务</strong><small>{{ mapStore.visiblePins.length }}</small></li>
            <li v-for="stat in categoryStats" :key="stat.key">
              <span class="legend-icon" :class="`cat-${stat.key}`"><AppIcon :name="stat.icon" /></span>
              <strong>{{ stat.label }}</strong>
              <small>{{ stat.count }}</small>
            </li>
          </ul>
        </section>

        <section class="float-card help-card">
          <h2>地图说明</h2>
          <p><span><AppIcon name="map-pin" /></span> 点击图标查看任务详情</p>
          <p><span><AppIcon name="hand" /></span> 拖动地图可移动视角</p>
          <p><span><AppIcon name="zoom-in" /></span> 滑动滚轮可缩放地图</p>
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
import { computed, onMounted, onUnmounted } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import MapContainer from "@/components/map/MapContainer.vue";
import TaskBeaconLayer from "@/components/map/TaskBeaconLayer.vue";
import PickerLayer from "@/components/map/PickerLayer.vue";
import AppIcon from "@/components/ui/AppIcon.vue";
import { useMapStore, type MapTaskPin } from "@/stores/map";
import type { CategoryType } from "@/types/map";

const route = useRoute();
const router = useRouter();
const mapStore = useMapStore();

const labels: Record<CategoryType, string> = {
  package: "代取快递",
  food: "代买餐食",
  move: "搬运重物",
  other: "其他",
};

const icons: Record<CategoryType, string> = {
  package: "package",
  food: "food",
  move: "move",
  other: "other",
};

const colors: Record<CategoryType, string> = {
  package: "#4d83c8",
  food: "#f1892d",
  move: "#52b478",
  other: "#8b75d7",
};

const visiblePanelPins = computed(() => {
  const pins = mapStore.pinsWithDistance as Array<MapTaskPin & { distanceKm: number | null }>;
  return pins;
});

const categoryStats = computed(() =>
  (Object.keys(labels) as CategoryType[]).map((key) => ({
    key,
    label: labels[key],
    icon: icons[key],
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

function locationText(pin: MapTaskPin) {
  return pin.to?.trim() || "校内地点";
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
  min-height: calc(100vh - 62px);
  padding: 18px 30px 28px;
  background: #fbfaf7;
  color: #252723;
  font-family: "Inter", "Noto Sans SC", "Microsoft YaHei", sans-serif;
  overflow: hidden;
}

.map-shell {
  position: relative;
  height: calc(100vh - 108px);
  min-height: 640px;
  max-width: 1620px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 400px minmax(0, 1fr);
  gap: 0;
}

.left-panel {
  display: flex;
  flex-direction: column;
  z-index: 5;
  margin-top: 0;
  padding: 22px 24px 20px;
  border: 1px solid #e8e5dc;
  border-right: 0;
  border-radius: 18px 0 0 18px;
  background: rgba(255, 253, 250, 0.95);
  box-shadow: 0 18px 44px rgba(65, 57, 46, 0.08);
  overflow: hidden;
}

.panel-toolbar {
  display: grid;
  grid-template-columns: minmax(82px, 1fr) 150px;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.panel-toolbar strong {
  color: #2d3428;
  font-size: 17px;
  font-weight: 950;
}

.panel-toolbar select {
  height: 36px;
  min-width: 0;
  padding: 0 11px;
  border: 1px solid #e6e2d9;
  border-radius: 8px;
  background: #fffdfa;
  color: #41433e;
  font: inherit;
  font-size: 12px;
  box-shadow: 0 6px 14px rgba(70, 63, 52, 0.025);
}

.panel-hint {
  margin: 0 0 14px;
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

.task-scroll {
  min-height: 0;
  flex: 1;
  overflow: auto;
  padding-right: 4px;
}

.task-scroll::-webkit-scrollbar {
  width: 6px;
}

.task-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.task-scroll::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(111, 131, 95, 0.26);
}

.nearby-list {
  display: grid;
  gap: 10px;
}

.nearby-card {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr) 112px;
  gap: 12px;
  align-items: center;
  min-height: 98px;
  padding: 13px 12px;
  border: 1px solid #ece8df;
  border-radius: 9px;
  background: #fff;
  box-shadow: none;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease, background 0.18s ease;
}

.nearby-card:hover,
.nearby-card.selected {
  border-color: #c7d4bd;
  background: #fff;
  box-shadow: 0 10px 24px rgba(91, 111, 76, 0.12);
  transform: translateY(-1px);
}

.pin-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  font-size: 22px;
  font-weight: 900;
}

.pin-icon .app-icon {
  width: 1em;
  height: 1em;
}

.cat-package { background: #edf4fb; color: #4d7db9; }
.cat-food { background: #fbf0df; color: #c77923; }
.cat-move { background: #eff5ec; color: #6d835f; }
.cat-other { background: #f0edfb; color: #8171c7; }

.nearby-main {
  min-width: 0;
  align-self: center;
  padding-top: 4px;
}

.nearby-main h3 {
  margin: 0 0 7px;
  overflow: hidden;
  color: #191b17;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  line-height: 1.2;
  font-weight: 950;
}

.nearby-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  color: #83857e;
  font-size: 12px;
  white-space: nowrap;
}

.location-text {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.location-text .app-icon {
  flex: 0 0 auto;
  font-size: 13px;
  color: #8c8f87;
}

.task-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 800;
}

.tag-package { background: #e8f1fb; color: #4778b4; }
.tag-food { background: #faecd8; color: #c97a25; }
.tag-move { background: #e8f0e3; color: #6d835f; }
.tag-other { background: #ebe7f8; color: #7b6cc4; }

.nearby-side footer {
  min-width: 0;
  max-width: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  color: #8a8c85;
  font-size: 12px;
  white-space: nowrap;
}

.nearby-side .mini-avatar {
  width: 21px;
  height: 21px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #e5d9cb;
  color: #596d4b;
  font-weight: 900;
}

.user-text {
  min-width: 0;
  max-width: 76px;
  display: grid;
  justify-items: end;
  line-height: 1.1;
}

.user-text b {
  display: block;
  max-width: 100%;
  overflow: hidden;
  color: #2d2f2a;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.credit {
  display: block;
  max-width: 100%;
  overflow: hidden;
  color: #df8a2f;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nearby-side {
  display: grid;
  justify-items: end;
  align-content: space-between;
  align-self: stretch;
  gap: 7px;
}

.nearby-side strong {
  color: #6f835f;
  font-size: 18px;
  font-weight: 950;
}

.nearby-side em {
  color: #83857e;
  font-size: 12px;
  font-style: normal;
}

.view-all {
  padding: 7px 8px 2px;
  color: #6f835f;
  font-size: 12px;
  text-align: center;
  text-decoration: none;
  font-weight: 800;
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
  top: 52px;
  right: 18px;
  z-index: 800;
  width: 222px;
  display: grid;
  gap: 12px;
}

.float-card {
  padding: 18px;
  border: 1px solid #ece8df;
  border-radius: 14px;
  background: rgba(255, 253, 250, 0.95);
  box-shadow: 0 18px 38px rgba(65, 57, 46, 0.12);
  backdrop-filter: blur(12px);
}

.float-card h2 {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 900;
}

.category-stats {
  display: grid;
  gap: 14px;
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
}

.category-stats li {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  align-items: center;
  gap: 10px;
}

.category-stats strong {
  font-size: 13px;
}

.category-stats small {
  color: #8b8d86;
  font-size: 12px;
}

.legend-icon {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  font-size: 15px;
}

.legend-icon.all {
  background: #eef3ea;
  color: #6f835f;
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
  display: grid;
  place-items: center;
  color: #6f835f;
}

.help-card .app-icon {
  width: 15px;
  height: 15px;
}

.picker-banner {
  position: absolute;
  left: 50%;
  bottom: 24px;
  z-index: 900;
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
  .map-page {
    padding: 18px 18px 24px;
    overflow: auto;
  }

  .map-shell {
    grid-template-columns: 360px minmax(0, 1fr);
    height: calc(100vh - 104px);
    min-height: 560px;
  }

  .right-stack {
    display: none;
  }
}
</style>
