<template>
  <aside class="floating-panel" :class="{ hidden: mapStore.pickerMode }">
    <section class="panel-section">
      <div class="section-header">
        <span class="section-title">任务类型</span>
        <button class="collapse-toggle" @click="typesOpen = !typesOpen">{{ typesOpen ? "⌃" : "⌄" }}</button>
      </div>
      <div v-if="typesOpen" class="type-list">
        <button
          class="type-item"
          :class="{ active: mapStore.activeFilter === 'all' }"
          @click="mapStore.setFilter('all')"
        >
          <span class="type-icon all">✦</span>
          <span class="type-label">全部任务</span>
          <span class="type-count">{{ totalOpen }}</span>
        </button>
        <button
          v-for="(c, key) in mapStore.categoryCounts"
          :key="key"
          class="type-item"
          :class="{ active: mapStore.activeFilter === key }"
          @click="mapStore.setFilter(key)"
        >
          <span class="type-icon" :style="{ background: c.color }">{{ categoryIcons[key] ?? "•" }}</span>
          <span class="type-label">{{ c.label }}</span>
          <span class="type-count">{{ c.count }}</span>
        </button>
      </div>
    </section>

    <section class="panel-section">
      <div class="section-header">
        <span class="section-title">数据概览</span>
      </div>
      <div class="overview-grid">
        <div v-for="s in mapStore.overviewStats" :key="s.label" class="ov-cell">
          <span class="ov-icon" :style="{ background: s.color }">{{ s.icon }}</span>
          <span class="ov-label">{{ s.label }}</span>
          <span class="ov-value">{{ s.value }}</span>
        </div>
      </div>
    </section>

    <section class="panel-section">
      <div class="section-header">
        <span class="section-title">图例说明</span>
      </div>
      <div class="legend-grid">
        <div v-for="item in legendItems" :key="item.label" class="legend-item">
          <span class="legend-dot" :style="{ background: item.color }">{{ item.icon }}</span>
          <span class="legend-label">{{ item.label }}</span>
        </div>
      </div>
    </section>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useMapStore } from "@/stores/map";
import { CATEGORY_COLORS, CATEGORY_ICONS } from "@/types/map";

const mapStore = useMapStore();
const typesOpen = ref(true);
const categoryIcons: Record<string, string> = CATEGORY_ICONS;

const totalOpen = computed(() =>
  Object.values(mapStore.categoryCounts).reduce((sum, c) => sum + c.count, 0),
);

const legendItems = [
  { label: "代取快递", icon: "📦", color: CATEGORY_COLORS.package },
  { label: "代买餐食", icon: "🍱", color: CATEGORY_COLORS.food },
  { label: "搬运重物", icon: "📦", color: CATEGORY_COLORS.move },
  { label: "其他", icon: "🔧", color: CATEGORY_COLORS.other },
];
</script>

<style scoped>
.floating-panel.hidden {
  display: none;
}

.floating-panel {
  position: absolute;
  top: 28px;
  left: 28px;
  z-index: 1000;
  width: 232px;
  max-height: calc(100% - 56px);
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 22px;
  overflow-y: auto;
  border: 1px solid rgba(31, 36, 48, 0.06);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 20px 55px rgba(31, 36, 48, 0.12);
  backdrop-filter: blur(18px);
}

.panel-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  color: #232937;
  font-size: 15px;
  font-weight: 900;
}

.collapse-toggle {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 8px;
  background: #f4f5f8;
  color: #8b92a0;
  cursor: pointer;
}

.type-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.type-item {
  min-height: 34px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0;
  border: none;
  background: transparent;
  color: #424b5d;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
}

.type-item.active .type-label {
  color: #6c5ce7;
  font-weight: 900;
}

.type-icon,
.legend-dot,
.ov-icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
}

.type-icon {
  width: 22px;
  height: 22px;
  border-radius: 8px;
}

.type-icon.all {
  background: #7c4dff;
}

.type-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 700;
}

.type-count {
  color: #535c6e;
  font-size: 12px;
  font-weight: 800;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 10px;
}

.ov-cell {
  min-width: 0;
  display: grid;
  grid-template-columns: 22px 1fr;
  column-gap: 7px;
  align-items: center;
}

.ov-icon {
  width: 22px;
  height: 22px;
  grid-row: span 2;
  border-radius: 8px;
  font-size: 10px;
}

.ov-label {
  color: #7d8493;
  font-size: 12px;
  line-height: 1.1;
}

.ov-value {
  color: #202633;
  font-size: 18px;
  font-weight: 900;
  line-height: 1.1;
}

.legend-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 10px;
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
  font-size: 10px;
}

.legend-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .floating-panel {
    top: 14px;
    left: 14px;
    width: 210px;
    max-height: calc(100% - 28px);
    padding: 16px;
  }
}
</style>
