import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type { FilterType } from "@/types/map";
import { buildings } from "@/data/buildings";
import { taskPins } from "@/data/taskPins";

export const useMapStore = defineStore("map", () => {
  const activeFilter = ref<FilterType>("all");
  const activeTaskId = ref<string | null>(null);
  const activeBuildingId = ref<string | null>(null);

  const visiblePins = computed(() => {
    if (activeFilter.value === "all") return taskPins;
    return taskPins.filter(
      (p) => p.filter === activeFilter.value || p.filter === "all"
    );
  });

  const activeTask = computed(() =>
    activeTaskId.value
      ? taskPins.find((p) => p.id === activeTaskId.value) ?? null
      : null
  );

  const activeBuilding = computed(() =>
    activeBuildingId.value
      ? buildings.find((b) => b.id === activeBuildingId.value) ?? null
      : null
  );

  function setFilter(filter: FilterType) {
    activeFilter.value = filter;
    activeTaskId.value = null;
  }

  function showTask(id: string) {
    activeTaskId.value = id;
    activeBuildingId.value = null;
  }

  function clearTask() {
    activeTaskId.value = null;
  }

  function openBuilding(id: string) {
    if (!id) return;
    activeBuildingId.value = activeBuildingId.value === id ? null : id;
    activeTaskId.value = null;
  }

  function closeBuilding() {
    activeBuildingId.value = null;
  }

  function clearAll() {
    activeTaskId.value = null;
    activeBuildingId.value = null;
  }

  return {
    activeFilter,
    activeTaskId,
    activeBuildingId,
    visiblePins,
    activeTask,
    activeBuilding,
    setFilter,
    showTask,
    clearTask,
    openBuilding,
    closeBuilding,
    clearAll,
  };
});
