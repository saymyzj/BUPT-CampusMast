<template>
  <div class="hud">
    <!-- Brand -->
    <div class="hud-card brand">
      <div class="brand-mark">CM</div>
      <div class="brand-meta">
        <strong>CampusMast</strong>
        <span>北邮西土城 · 任务地图</span>
      </div>
    </div>

    <!-- Toolbar filters -->
    <div class="hud-card toolbar">
      <button
        v-for="f in FILTERS"
        :key="f.id"
        class="toolbar-chip"
        :class="{ active: mapStore.activeFilter === f.id }"
        @click="mapStore.setFilter(f.id)"
      >
        {{ f.label }}
      </button>
    </div>

    <!-- Status pill -->
    <div class="hud-card status-pill">
      <span class="status-dot"></span>
      <span class="status-value">{{ mapStore.visiblePins.length }} 点位</span>
      <span class="status-divider"></span>
      <span class="status-value">¥328</span>
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
  position: fixed;
  top: 18px;
  left: 18px;
  width: 320px;
  z-index: 30;
  display: grid;
  gap: 14px;
  pointer-events: none;
}

.toolbar {
  min-width: 0;
}

.hud-card {
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  background: rgba(245, 239, 226, 0.88);
  border: 2px solid rgba(31, 42, 58, 0.08);
  box-shadow: 6px 6px 0 rgba(31, 34, 48, 0.1);
  pointer-events: auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 24px;
}

.brand-mark {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: #1f2230;
  color: #f0c94a;
  font-family: "Fredoka", sans-serif;
  font-weight: 700;
  font-size: 16px;
  letter-spacing: -0.03em;
}

.brand-meta strong {
  display: block;
  font-family: "Fredoka", sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: #1f2230;
  letter-spacing: -0.03em;
}

.brand-meta span {
  display: block;
  font-size: 11px;
  color: #728097;
  font-weight: 500;
  margin-top: 1px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 24px;
}

.toolbar-chip {
  border: 2px solid transparent;
  background: transparent;
  color: #728097;
  padding: 8px 14px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 180ms ease;
  font-family: "Fredoka", "Noto Sans SC", sans-serif;
  font-size: 13px;
  font-weight: 600;
}

.toolbar-chip:hover {
  background: rgba(31, 34, 48, 0.06);
  color: #1f2230;
}

.toolbar-chip.active {
  background: #1f2230;
  color: #f0c94a;
  border-color: #1f2230;
  box-shadow: 3px 3px 0 rgba(31, 34, 48, 0.15);
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 24px;
  justify-content: space-between;
}

.status-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #6ca365;
  box-shadow: 0 0 0 5px rgba(108, 163, 101, 0.15);
  animation: dot-pulse 2s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { box-shadow: 0 0 0 4px rgba(108, 163, 101, 0.15); }
  50% { box-shadow: 0 0 0 8px rgba(108, 163, 101, 0.08); }
}

.status-label {
  font-size: 11px;
  color: #728097;
  font-weight: 600;
}

.status-value {
  font-size: 13px;
  font-weight: 700;
  color: #1f2230;
  font-family: "Fredoka", sans-serif;
}

.status-divider {
  width: 1px;
  height: 16px;
  background: rgba(31, 34, 48, 0.15);
}

@media (max-width: 1180px) {
  .hud {
    width: auto;
    right: 18px;
  }
}
</style>
