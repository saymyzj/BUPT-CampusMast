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
  width: min(860px, calc(100vw - 372px));
  border-radius: 28px;
  overflow: hidden;
  box-shadow: 0 22px 48px rgba(20, 29, 40, 0.18);
  border: 1px solid rgba(31, 42, 58, 0.08);
  z-index: 1;
}

.map-container :deep(.leaflet-container) {
  background: #e8edf0;
  font-family: "Noto Sans SC", sans-serif;
}

.map-container :deep(.leaflet-control-attribution) {
  background: rgba(245, 239, 226, 0.88);
  border-radius: 12px 0 0 0;
  color: #586579;
  font-size: 11px;
}

.map-container :deep(.leaflet-control-zoom) {
  border: none;
  box-shadow: 0 12px 24px rgba(20, 29, 40, 0.14);
}

.map-container :deep(.leaflet-control-zoom a) {
  width: 34px;
  height: 34px;
  line-height: 34px;
  color: #1f2230;
  background: rgba(245, 239, 226, 0.96);
  border: 1px solid rgba(31, 42, 58, 0.1);
}

.map-container :deep(.leaflet-control-zoom a:hover) {
  background: #fffaf2;
}

@media (max-width: 1180px) {
  .map-container {
    left: 18px;
    width: auto;
    top: 180px;
  }
}
</style>
