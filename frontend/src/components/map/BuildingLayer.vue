<template>
  <div style="display: none"></div>
</template>

<script setup lang="ts">
import { watch, onUnmounted } from "vue";
import L from "leaflet";
import { buildings } from "@/data/buildings";
import { useMapStore } from "@/stores/map";
import { useMapContext } from "@/composables/useLeafletMap";

const { map, toLatLng } = useMapContext();
const mapStore = useMapStore();
const layers: L.Layer[] = [];

const BUILDING_COLORS: Record<string, string> = {
  teaching: "#4970c8",
  teaching2: "#4970c8",
  library: "#d6a74f",
  research: "#d87379",
  canteen: "#d87379",
  dorm: "#6c8c78",
  admin: "#5b667b",
  service: "#8a67c8",
  logistics: "#4970c8",
  sports: "#d6a74f",
  green: "#89a35a",
  residential: "#8f9189",
};

function createLayers(m: L.Map) {
  clearLayers();

  for (const b of buildings) {
    const color = BUILDING_COLORS[b.type] ?? "#4970c8";
    const open = () => mapStore.openBuilding(b.id);

    if (b.polygon?.length) {
      const polygon = L.polygon(b.polygon.map(toLatLng), {
        color,
        weight: b.core ? 2 : 1.5,
        opacity: b.core ? 0.7 : 0.45,
        fillColor: color,
        fillOpacity: b.core ? 0.14 : 0.05,
        className: "campus-building-shape",
        bubblingMouseEvents: false,
      }).addTo(m);

      polygon.on("mouseover", () => {
        polygon.setStyle({
          weight: b.core ? 2.6 : 2,
          opacity: 0.9,
          fillOpacity: b.core ? 0.2 : 0.09,
        });
      });
      polygon.on("mouseout", () => {
        polygon.setStyle({
          weight: b.core ? 2 : 1.5,
          opacity: b.core ? 0.7 : 0.45,
          fillOpacity: b.core ? 0.14 : 0.05,
        });
      });
      polygon.on("click", (e) => {
        L.DomEvent.stopPropagation(e);
        open();
      });

      layers.push(polygon);
      continue;
    }

    const marker = L.circleMarker(toLatLng(b.center), {
      radius: b.core ? 14 : 10,
      color,
      weight: 2,
      opacity: 0.75,
      fillColor: color,
      fillOpacity: 0.22,
      bubblingMouseEvents: false,
    }).addTo(m);

    marker.on("mouseover", () => marker.setStyle({ radius: b.core ? 16 : 12, fillOpacity: 0.3, opacity: 0.95 }));
    marker.on("mouseout", () => marker.setStyle({ radius: b.core ? 14 : 10, fillOpacity: 0.22, opacity: 0.75 }));
    marker.on("click", (e) => {
      L.DomEvent.stopPropagation(e);
      open();
    });

    layers.push(marker);
  }
}

function clearLayers() {
  layers.forEach((layer) => layer.remove());
  layers.length = 0;
}

watch(map, (m) => {
  if (m) createLayers(m);
}, { immediate: true });

onUnmounted(clearLayers);
</script>

<style>
</style>
