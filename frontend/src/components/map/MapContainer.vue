<template>
  <div ref="containerEl" class="map-container"></div>
  <slot />
</template>

<script setup lang="ts">
import { ref } from "vue";
import { provideLeafletMap } from "@/composables/useLeafletMap";
import { useMapStore } from "@/stores/map";

const containerEl = ref<HTMLElement | null>(null);
const { map } = provideLeafletMap(containerEl);
const mapStore = useMapStore();

// Close popups on map background click
import { watch } from "vue";
watch(map, (m) => {
  if (m) {
    m.on("click", () => mapStore.clearAll());
  }
});
</script>

<style scoped>
.map-container {
  position: absolute;
  top: 18px;
  right: 18px;
  bottom: 18px;
  left: 352px;
  border-radius: 22px;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(20, 29, 40, 0.1);
  border: 1px solid rgba(31, 42, 58, 0.05);
  z-index: 1;
  animation: map-reveal 600ms cubic-bezier(0.22, 1, 0.36, 1) 60ms both;
}

@keyframes map-reveal {
  from { opacity: 0; }
  to { opacity: 1; }
}

.map-container :deep(.leaflet-container) {
  background: #e8edf0;
  font-family: "Noto Sans SC", sans-serif;
}

.map-container :deep(.leaflet-control-attribution) {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 10px 0 0 0;
  color: #8d96a5;
  font-size: 10px;
  padding: 3px 8px;
}

.map-container :deep(.leaflet-control-zoom) {
  border: none;
  box-shadow: 0 4px 16px rgba(20, 29, 40, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.map-container :deep(.leaflet-control-zoom a) {
  width: 36px;
  height: 36px;
  line-height: 36px;
  color: #1f2230;
  background: rgba(255, 255, 255, 0.92);
  border: none;
  border-bottom: 1px solid rgba(31, 42, 58, 0.06);
}

.map-container :deep(.leaflet-control-zoom a:last-child) {
  border-bottom: none;
}

.map-container :deep(.leaflet-control-zoom a:hover) {
  background: #fff;
}
</style>
