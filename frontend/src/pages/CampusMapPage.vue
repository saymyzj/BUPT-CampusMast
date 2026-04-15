<template>
  <div class="map-page font-body">
    <MapContainer>
      <BuildingLayer />
      <TaskBeaconLayer />
      <BuildingInfoCard />
    </MapContainer>
    <MapHUD />
    <MapLegend />
    <PostTaskFAB />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import MapContainer from "@/components/map/MapContainer.vue";
import BuildingLayer from "@/components/map/BuildingLayer.vue";
import TaskBeaconLayer from "@/components/map/TaskBeaconLayer.vue";
import MapHUD from "@/components/map/MapHUD.vue";
import BuildingInfoCard from "@/components/map/BuildingInfoCard.vue";
import MapLegend from "@/components/map/MapLegend.vue";
import PostTaskFAB from "@/components/map/PostTaskFAB.vue";
import { useMapStore } from "@/stores/map";

const mapStore = useMapStore();

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") mapStore.clearAll();
}

onMounted(() => document.addEventListener("keydown", onKeydown));
onUnmounted(() => document.removeEventListener("keydown", onKeydown));
</script>

<style scoped>
.map-page {
  position: fixed;
  inset: 0;
  overflow: hidden;
  background: linear-gradient(180deg, #f5efe2 0%, #ede5d6 100%);
}
</style>
