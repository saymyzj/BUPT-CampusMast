<template>
  <div class="hud">
    <!-- Brand -->
    <div class="brand">
      <div class="brand-mark">CM</div>
      <div class="brand-meta">
        <strong>CampusMast</strong>
        <span>北邮西土城 · 任务地图</span>
      </div>
    </div>

    <div class="divider"></div>

    <!-- Filters -->
    <div class="filters">
      <button
        v-for="f in FILTERS"
        :key="f.id"
        class="filter-btn"
        :class="{ active: mapStore.activeFilter === f.id }"
        @click="mapStore.setFilter(f.id)"
      >
        {{ f.label }}
      </button>
    </div>

    <div class="divider"></div>

    <!-- Stats -->
    <div class="stats">
      <div class="stat-group">
        <span class="stat-dot"></span>
        <span class="stat-number">{{ mapStore.visiblePins.length }}</span>
        <span class="stat-unit">个任务</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-group">
        <span class="stat-number gold">¥328</span>
        <span class="stat-unit">赏金池</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMapStore } from "@/stores/map";
import { FILTERS } from "@/data/mapConfig";

const mapStore = useMapStore();
</script>

<style scoped>
.hud {
  padding: 22px 20px 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: #1f2230;
  color: #f0c94a;
  font-family: "Fredoka", sans-serif;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: -0.03em;
  flex-shrink: 0;
}

.brand-meta strong {
  display: block;
  font-family: "Fredoka", sans-serif;
  font-size: 17px;
  font-weight: 700;
  color: #1f2230;
  letter-spacing: -0.02em;
}

.brand-meta span {
  display: block;
  font-size: 11px;
  color: #919bab;
  font-weight: 500;
  margin-top: 2px;
}

.divider {
  height: 1px;
  background: rgba(31, 42, 58, 0.06);
  margin: 16px 0;
}

.filters {
  display: flex;
  gap: 6px;
}

.filter-btn {
  flex: 1;
  border: 1.5px solid rgba(31, 42, 58, 0.08);
  background: transparent;
  color: #7b8698;
  padding: 9px 6px;
  border-radius: 12px;
  cursor: pointer;
  font-family: "Fredoka", "Noto Sans SC", sans-serif;
  font-size: 12px;
  font-weight: 600;
  transition: all 220ms cubic-bezier(0.22, 1, 0.36, 1);
  white-space: nowrap;
}

.filter-btn:hover {
  border-color: rgba(31, 42, 58, 0.15);
  color: #1f2230;
  background: rgba(31, 42, 58, 0.03);
}

.filter-btn.active {
  background: #1f2230;
  color: #f0c94a;
  border-color: #1f2230;
  box-shadow: 0 2px 10px rgba(31, 34, 48, 0.18);
  transform: scale(1.02);
}

.stats {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-group {
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.stat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #6ca365;
  box-shadow: 0 0 0 3px rgba(108, 163, 101, 0.15);
  animation: dot-pulse 2.5s ease-in-out infinite;
  align-self: center;
}

@keyframes dot-pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(108, 163, 101, 0.15); }
  50% { box-shadow: 0 0 0 6px rgba(108, 163, 101, 0.06); }
}

.stat-number {
  font-family: "Fredoka", sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: #1f2230;
  letter-spacing: -0.02em;
}

.stat-number.gold {
  color: #c49a2e;
}

.stat-unit {
  font-size: 12px;
  color: #919bab;
  font-weight: 500;
}

.stat-sep {
  width: 1px;
  height: 22px;
  background: rgba(31, 42, 58, 0.07);
}
</style>
