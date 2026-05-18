<template>
  <Transition name="panel-slide">
    <aside v-if="mapStore.activeBuilding" class="building-panel">
      <div class="panel-header">
        <div class="panel-kicker">楼宇 / 楼层信息</div>
        <div class="panel-title-row">
          <div>
            <h3 class="panel-title">{{ mapStore.activeBuilding.name }}</h3>
            <p class="panel-summary">{{ mapStore.activeBuilding.summary }}</p>
          </div>
          <button class="panel-close" @click.stop="closePanel">&times;</button>
        </div>
      </div>

      <div v-if="floors.length" class="panel-body">
        <div class="floor-tabs">
          <button
            v-for="floor in floors"
            :key="floor.id"
            class="floor-tab"
            :class="{ active: floor.id === activeFloorId }"
            @click="activeFloorId = floor.id"
          >
            {{ floor.name }}
          </button>
        </div>

        <div v-if="activeFloor" class="floor-content">
          <div class="highlight-list">
            <span v-for="item in activeFloor.highlights" :key="item" class="highlight-pill">
              {{ item }}
            </span>
          </div>
          <p class="floor-summary">{{ activeFloor.summary }}</p>

          <div class="floor-zone-card">
            <div class="zone-title">楼内示意</div>
            <div class="zone-layout">
              <div class="zone-block block-wide">主要活动区</div>
              <div class="zone-block block-core">楼梯 / 电梯</div>
              <div class="zone-block block-left">公共区</div>
              <div class="zone-block block-right">功能区</div>
            </div>
          </div>

          <div class="poi-list">
            <div v-for="poi in activeFloor.pois" :key="poi.name" class="poi-item">
              <span class="poi-dot" :style="{ background: poi.color }"></span>
              <div>
                <strong>{{ poi.name }}</strong>
                <span>{{ poi.desc }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="panel-empty">
        <p>该楼宇还未补充楼层示意，但交互结构已经预留，可继续扩展。</p>
      </div>
    </aside>
  </Transition>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useMapStore } from "@/stores/map";

const mapStore = useMapStore();
const activeFloorId = ref<string | null>(null);

const floors = computed(() => mapStore.activeBuilding?.floors ?? []);

const activeFloor = computed(() => {
  if (!floors.value.length) return null;
  return floors.value.find((floor) => floor.id === activeFloorId.value) ?? floors.value[0];
});

function closePanel() {
  mapStore.closeBuilding();
}

watch(
  () => mapStore.activeBuildingId,
  () => {
    activeFloorId.value = floors.value[0]?.id ?? null;
  },
  { immediate: true }
);
</script>

<style scoped>
.building-panel {
  position: fixed;
  top: 18px;
  right: 18px;
  bottom: 18px;
  width: 356px;
  z-index: 1200;
  border-radius: 28px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(31, 42, 58, 0.05);
  box-shadow: 0 20px 48px rgba(20, 29, 40, 0.12), 0 2px 6px rgba(20, 29, 40, 0.04);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 20px 20px 16px;
  border-bottom: 1px solid rgba(31, 42, 58, 0.08);
}

.panel-kicker {
  font-size: 11px;
  color: #728097;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-title-row {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  gap: 14px;
}

.panel-title {
  font-size: 24px;
  font-weight: 800;
  color: #1f2230;
  letter-spacing: -0.04em;
  line-height: 1.15;
}

.panel-summary {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: #6d7888;
}

.panel-close {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 12px;
  background: rgba(31, 42, 58, 0.06);
  color: #1f2230;
  font-size: 18px;
  cursor: pointer;
  flex-shrink: 0;
}

.panel-body {
  padding: 18px 20px 20px;
  overflow-y: auto;
  display: grid;
  gap: 16px;
}

.floor-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.floor-tab {
  border: none;
  border-radius: 999px;
  background: rgba(31, 42, 58, 0.06);
  color: #5a6679;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

.floor-tab.active {
  background: #1f2230;
  color: #fff;
}

.floor-content {
  display: grid;
  gap: 14px;
}

.highlight-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.highlight-pill {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(31, 42, 58, 0.06);
  color: #405068;
  font-size: 11px;
  font-weight: 700;
}

.floor-summary {
  font-size: 13px;
  line-height: 1.6;
  color: #6d7888;
}

.floor-zone-card {
  padding: 14px;
  border-radius: 20px;
  background: rgba(225, 235, 239, 0.54);
  border: 1px solid rgba(31, 42, 58, 0.06);
}

.zone-title {
  font-size: 12px;
  font-weight: 800;
  color: #1f2230;
  margin-bottom: 10px;
}

.zone-layout {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 8px;
}

.zone-block {
  border-radius: 16px;
  padding: 14px 12px;
  font-size: 12px;
  font-weight: 800;
  color: #1f2230;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(31, 42, 58, 0.06);
  text-align: center;
}

.block-wide {
  grid-column: span 2;
  background: rgba(73, 112, 200, 0.12);
}

.block-core {
  background: rgba(214, 167, 79, 0.18);
}

.block-left {
  background: rgba(216, 115, 121, 0.12);
}

.block-right {
  background: rgba(108, 140, 120, 0.12);
}

.poi-list {
  display: grid;
  gap: 10px;
}

.poi-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(245, 243, 238, 0.85);
  border: 1px solid rgba(31, 42, 58, 0.06);
}

.poi-dot {
  width: 10px;
  height: 10px;
  margin-top: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}

.poi-item strong {
  display: block;
  font-size: 13px;
  font-weight: 800;
  color: #1f2230;
}

.poi-item span {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.55;
  color: #6d7888;
}

.panel-empty {
  padding: 20px;
  font-size: 13px;
  line-height: 1.6;
  color: #6d7888;
}

.panel-slide-enter-active {
  animation: panel-in 300ms cubic-bezier(0.22, 1, 0.36, 1);
}

.panel-slide-leave-active {
  animation: panel-in 200ms cubic-bezier(0.22, 1, 0.36, 1) reverse;
}

@keyframes panel-in {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@media (max-width: 1180px) {
  .building-panel {
    top: auto;
    left: 18px;
    right: 18px;
    bottom: 18px;
    width: auto;
    max-height: 58vh;
  }
}
</style>
