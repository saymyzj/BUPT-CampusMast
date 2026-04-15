<template>
  <div class="map-page font-body">
    <aside class="sidebar">
      <MapHUD />
      <div class="sidebar-grow"></div>
      <MapLegend />
      <PostTaskFAB />
    </aside>
    <MapContainer>
      <BuildingLayer />
      <TaskBeaconLayer />
      <BuildingInfoCard />
    </MapContainer>
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
  background: #e9e3d7;
}

.sidebar {
  position: absolute;
  top: 18px;
  left: 18px;
  bottom: 18px;
  width: 320px;
  border-radius: 22px;
  background: #faf7f1;
  border: 1px solid rgba(31, 42, 58, 0.04);
  box-shadow: 0 8px 30px rgba(20, 29, 40, 0.06);
  z-index: 20;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: sidebar-in 480ms cubic-bezier(0.22, 1, 0.36, 1);
}

.sidebar-grow {
  flex: 1;
}

@keyframes sidebar-in {
  from {
    opacity: 0;
    transform: translateX(-14px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
