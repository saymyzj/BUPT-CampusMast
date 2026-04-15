<template>
  <div class="map-legend font-display">
    <div class="legend-title">任务图例</div>
    <div class="legend-row" v-for="item in items" :key="item.label">
      <span class="legend-dot" :style="{ background: item.color }"></span>
      {{ item.label }}
    </div>
  </div>
</template>

<script setup lang="ts">
const items = [
  { label: "代取/代送", color: "#2553d4" },
  { label: "代买餐食", color: "#e4572e" },
  { label: "搬运协助", color: "#d6a74f" },
  { label: "占座/打印/其他", color: "#5c715e" },
];
</script>

<style scoped>
.map-legend {
  position: fixed;
  left: 18px;
  bottom: 108px;
  z-index: 24;
  padding: 14px 18px;
  width: 320px;
  border-radius: 24px;
  background: rgba(245, 239, 226, 0.9);
  border: 2px solid rgba(31, 42, 58, 0.08);
  box-shadow: 4px 4px 0 rgba(31, 34, 48, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: grid;
  gap: 8px;
}

.legend-title {
  font-size: 11px;
  color: #728097;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #1f2230;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 2px solid rgba(255, 255, 255, 0.6);
}

@media (max-width: 1180px) {
  .map-legend {
    width: auto;
    left: 18px;
    right: 18px;
    bottom: 18px;
  }
}
</style>
