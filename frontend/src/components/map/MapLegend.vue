<template>
  <div class="legend font-display">
    <div class="legend-items">
      <div class="legend-item" v-for="item in items" :key="item.label">
        <span class="legend-dot" :style="{ background: item.color }"></span>
        <span class="legend-label">{{ item.label }}</span>
      </div>
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
.legend {
  padding: 0 20px 12px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-label {
  font-size: 11px;
  color: #919bab;
  font-weight: 500;
}
</style>
