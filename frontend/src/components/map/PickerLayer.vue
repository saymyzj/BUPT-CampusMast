<template>
  <div style="display: none"></div>
</template>

<script setup lang="ts">
import { watch, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import L from "leaflet";
import { useMapStore } from "@/stores/map";
import { useMapContext } from "@/composables/useLeafletMap";

const router = useRouter();
const { map } = useMapContext();
const mapStore = useMapStore();
const pickerMarker = ref<L.Marker | null>(null);

function updatePick(lat: number, lng: number) {
  mapStore.pickPoint(lat, lng, `${lat.toFixed(5)}, ${lng.toFixed(5)}`);
}

function onMapClick(e: L.LeafletMouseEvent) {
  if (!mapStore.pickerMode) return;
  const { lat, lng } = e.latlng;

  if (pickerMarker.value) {
    pickerMarker.value.remove();
  }

  const m = map.value!;
  pickerMarker.value = L.marker([lat, lng], {
    icon: L.divIcon({
      html: '<div style="width:28px;height:28px;border-radius:50% 50% 50% 0;background:#b24a3a;border:3px solid #fff;box-shadow:0 4px 14px rgba(178,74,58,0.45);transform:rotate(-45deg);display:flex;align-items:center;justify-content:center;"><div style="width:8px;height:8px;border-radius:50%;background:#fff;transform:rotate(45deg);"></div></div>',
      className: "picker-marker-shell",
      iconSize: L.point(28, 28),
      iconAnchor: L.point(14, 26),
    }),
    draggable: true,
  }).addTo(m);

  pickerMarker.value.on("dragend", () => {
    const ll = pickerMarker.value!.getLatLng();
    updatePick(ll.lat, ll.lng);
  });

  updatePick(lat, lng);
}

watch(
  [map, () => mapStore.pickerMode],
  ([m, picker]) => {
    if (!m) return;
    if (picker) {
      m.on("click", onMapClick);
      m.getContainer().style.cursor = "crosshair";
    } else {
      m.off("click", onMapClick);
      m.getContainer().style.cursor = "";
      if (pickerMarker.value) {
        pickerMarker.value.remove();
        pickerMarker.value = null;
      }
    }
  },
  { immediate: true }
);

onUnmounted(() => {
  map.value?.off("click", onMapClick);
  if (pickerMarker.value) {
    pickerMarker.value.remove();
    pickerMarker.value = null;
  }
});
</script>

<style>
.picker-marker-shell {
  background: transparent !important;
  border: none !important;
}
</style>
