<template>
  <div class="map-wrapper">
    <div ref="containerEl" class="map-container"></div>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { provideLeafletMap } from "@/composables/useLeafletMap";
import { useMapStore } from "@/stores/map";

const containerEl = ref<HTMLElement | null>(null);
const { map } = provideLeafletMap(containerEl);
const mapStore = useMapStore();

// Close popups on map background click
watch(map, (m) => {
  if (m) {
    m.on("click", () => mapStore.clearAll());
  }
});
</script>

<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #edf1f5;
}

.map-container {
  width: 100%;
  height: 100%;
}

.map-container :deep(.leaflet-container) {
  background: #edf1f5;
  font-family: "Noto Sans SC", sans-serif;
}

.map-container :deep(.leaflet-control-attribution) {
  background: rgba(255, 255, 255, 0.78);
  border-radius: 12px 0 0 0;
  color: #8b94a3;
  font-size: 10px;
  padding: 3px 8px;
}

.map-container :deep(.leaflet-control-zoom) {
  border: none;
  box-shadow: 0 12px 32px rgba(31, 36, 48, 0.14);
  border-radius: 12px;
  overflow: hidden;
  margin-right: 22px;
  margin-bottom: 24px;
}

.map-container :deep(.leaflet-control-zoom a) {
  width: 42px;
  height: 42px;
  line-height: 42px;
  color: #1f2230;
  background: rgba(255, 255, 255, 0.96);
  border: none;
  border-bottom: 1px solid rgba(31, 42, 58, 0.06);
  font-weight: 800;
}

.map-container :deep(.leaflet-control-zoom a:last-child) {
  border-bottom: none;
}

.map-container :deep(.leaflet-control-zoom a:hover) {
  background: #fff;
}

.map-container :deep(.leaflet-tile-pane) {
  filter: saturate(0.82) brightness(1.04) contrast(0.92);
}
</style>
