import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { CATEGORY_COLORS, CATEGORY_LABELS, type CategoryType } from "@/types/map";
import { listTasks } from "@/api/modules/task";
import { listCampusBuildings } from "@/api/modules/map";
import { useAuthStore } from "@/stores/auth";
import { isTaskVisible } from "@/utils/taskVisibility";
import type { Task, CampusBuilding } from "@/types/api";

export interface MapTaskPin {
  id: string;
  buildingCode: string;
  category: CategoryType;
  reward: string;
  timeLeft: string;
  title: string;
  summary: string;
  shortLabel: string;
  position: [number, number];
  label: string;
  action: string;
  requesterName: string;
  requesterCreditScore: number;
  from?: string;
  to?: string;
}

function mapCategory(apiCategory: string): CategoryType {
  if (apiCategory === "package" || apiCategory === "food" || apiCategory === "move" || apiCategory === "other") {
    return apiCategory;
  }
  return "other";
}

function haversineKm(a: { lat: number; lng: number }, b: { lat: number; lng: number }): number {
  const R = 6371;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLng = ((b.lng - a.lng) * Math.PI) / 180;
  const sinLat = Math.sin(dLat / 2);
  const sinLng = Math.sin(dLng / 2);
  const h =
    sinLat * sinLat +
    Math.cos((a.lat * Math.PI) / 180) *
      Math.cos((b.lat * Math.PI) / 180) *
      sinLng * sinLng;
  return R * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
}

function isCoordinatePair(value: unknown): value is number[] {
  return Array.isArray(value) && value.length >= 2 && typeof value[0] === "number" && typeof value[1] === "number";
}

function pointInRing(lat: number, lng: number, ring: number[][]): boolean {
  if (ring.length < 3) return false;
  let inside = false;
  let j = ring.length - 1;
  for (let i = 0; i < ring.length; i += 1) {
    const [yi, xi] = ring[i];
    const [yj, xj] = ring[j];
    const intersects = xi > lng !== xj > lng && lat < ((yj - yi) * (lng - xi)) / (xj - xi) + yi;
    if (intersects) inside = !inside;
    j = i;
  }
  return inside;
}

function buildingContainsPoint(building: CampusBuilding, lat: number, lng: number): boolean {
  const polygon = building.polygon;
  if (!Array.isArray(polygon) || polygon.length === 0) return false;
  if (isCoordinatePair(polygon[0])) return pointInRing(lat, lng, polygon as number[][]);
  return (polygon as number[][][]).some((ring) => pointInRing(lat, lng, ring));
}

function computeTimeLeft(deadline: string): string {
  const diff = new Date(deadline).getTime() - Date.now();
  if (diff <= 0) return "已截止";
  const h = Math.floor(diff / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  if (h > 24) {
    const d = new Date(deadline);
    return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  }
  if (h > 0) return `${h} 小时`;
  if (m > 0) return `${m} 分钟`;
  return "马上截止";
}

export const useMapStore = defineStore("map", () => {
  const authStore = useAuthStore();

  const activeFilter = ref<string>("all");
  const activeTaskId = ref<string | null>(null);
  const activeBuildingId = ref<string | null>(null);
  const focusTaskId = ref<string | null>(null);

  const pickerMode = ref(false);
  const pickedLat = ref<number | null>(null);
  const pickedLng = ref<number | null>(null);
  const pickedLabel = ref<string | null>(null);
  const pickedBuildingCode = ref<string | null>(null);

  const apiTasks = ref<Task[]>([]);
  const buildings = ref<CampusBuilding[]>([]);
  const tasksLoading = ref(false);
  const tasksError = ref("");

  const sidebarCollapsed = ref(false);
  const userLocation = ref<{ lat: number; lng: number } | null>(null);
  const nearbyOnly = ref(false);

  const buildingCoords = computed(() => {
    const map = new Map<string, { lat: number; lng: number; name: string }>();
    for (const b of buildings.value) {
      map.set(b.code, { lat: b.latitude, lng: b.longitude, name: b.name });
    }
    return map;
  });

  const openTasks = computed(() =>
    apiTasks.value.filter((t) => t.status === "PENDING" && isTaskVisible(t)),
  );

  const visiblePins = computed<MapTaskPin[]>(() => {
    const defaultPos: [number, number] = [39.961, 116.351];
    const raw = openTasks.value
      .filter((t) => t.requester.id !== authStore.userId)
      .map((t): MapTaskPin => {
        let pos: [number, number];
        const building = buildingCoords.value.get(t.buildingCode);
        if (t.latitude != null && t.longitude != null) {
          pos = [t.latitude, t.longitude];
        } else {
          pos = building ? [building.lat, building.lng] : defaultPos;
        }
        const cat = mapCategory(t.category);
        const summary = t.description.length > 42 ? `${t.description.slice(0, 42)}...` : t.description;
        return {
          id: t.id,
          buildingCode: t.buildingCode,
          category: cat,
          reward: `¥${parseFloat(t.reward).toFixed(2)}`,
          timeLeft: computeTimeLeft(t.deadline),
          title: t.title,
          summary,
          shortLabel: CATEGORY_LABELS[cat].slice(0, 4),
          position: pos,
          label: CATEGORY_LABELS[cat],
          action: "接单",
          requesterName: t.requester.nickname,
          requesterCreditScore: t.requester.overallCreditScore,
          from: building?.name,
          to: t.locationDetail || "校内地点",
        };
      });

    const filtered = activeFilter.value === "all" ? raw : raw.filter((p) => p.category === activeFilter.value);
    if (!nearbyOnly.value || !userLocation.value) return filtered;
    return filtered.filter((p) => haversineKm(userLocation.value!, { lat: p.position[0], lng: p.position[1] }) <= 2);
  });

  const pinsWithDistance = computed(() =>
    visiblePins.value.map((p) => {
      let distanceKm: number | null = null;
      if (userLocation.value) {
        distanceKm = haversineKm(userLocation.value, { lat: p.position[0], lng: p.position[1] });
      }
      return { ...p, distanceKm };
    })
  );

  const categoryCounts = computed(() => {
    const counts: Record<string, { label: string; color: string; count: number }> = {};
    for (const t of openTasks.value) {
      const cat = mapCategory(t.category);
      if (!counts[cat]) {
        counts[cat] = { label: CATEGORY_LABELS[cat], color: CATEGORY_COLORS[cat], count: 0 };
      }
      counts[cat].count++;
    }
    return counts;
  });

  const overviewStats = computed(() => [
    { icon: "🟣", value: openTasks.value.length, label: "今日活跃", color: "#7c4dff" },
    { icon: "🧡", value: apiTasks.value.filter((t) => t.status === "IN_PROGRESS").length, label: "待接任务", color: "#ff8a34" },
    { icon: "🟢", value: apiTasks.value.filter((t) => t.status === "COMPLETED").length, label: "已完成", color: "#32c483" },
    { icon: "⭐", value: "98%", label: "好评率", color: "#ffca3a" },
  ]);

  const activeTask = computed(() =>
    activeTaskId.value
      ? visiblePins.value.find((p) => p.id === activeTaskId.value) ?? null
      : null
  );

  const activeBuilding = computed(() =>
    activeBuildingId.value
      ? buildings.value.find((b) => b.code === activeBuildingId.value) ?? null
      : null
  );

  function setFilter(filter: string) {
    activeFilter.value = filter;
    activeTaskId.value = null;
  }

  function setFocus(id: string | null) {
    focusTaskId.value = id;
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

  function enterPickerMode() {
    pickerMode.value = true;
    pickedLat.value = null;
    pickedLng.value = null;
    pickedLabel.value = null;
    pickedBuildingCode.value = null;
  }

  function leavePickerMode() {
    pickerMode.value = false;
    pickedLat.value = null;
    pickedLng.value = null;
    pickedLabel.value = null;
    pickedBuildingCode.value = null;
  }

  function pickPoint(lat: number, lng: number, label: string) {
    pickedLat.value = lat;
    pickedLng.value = lng;
    const nearest = findNearestBuilding(lat, lng);
    pickedBuildingCode.value = nearest?.code ?? null;
    pickedLabel.value = nearest ? `${nearest.name}附近 (${lat.toFixed(5)}, ${lng.toFixed(5)})` : label;
  }

  function removeTask(id: string) {
    apiTasks.value = apiTasks.value.filter((t) => t.id !== id);
  }

  async function fetchMapData() {
    if (tasksLoading.value) return;
    tasksLoading.value = true;
    tasksError.value = "";
    try {
      const [tasksResult, buildingsResult] = await Promise.all([
        listTasks({ limit: 100, sortBy: "newest" }),
        listCampusBuildings(),
      ]);
      apiTasks.value = tasksResult.data;
      buildings.value = buildingsResult;
    } catch (err: any) {
      tasksError.value = err?.response?.data?.error?.message || "加载地图数据失败";
    } finally {
      tasksLoading.value = false;
    }
  }

  function findNearestBuilding(lat: number, lng: number): { code: string; name: string } | null {
    const containing = buildings.value.find((building) => buildingContainsPoint(building, lat, lng));
    if (containing) return { code: containing.code, name: containing.name };

    let minDist = Infinity;
    let nearest: { code: string; name: string } | null = null;
    for (const b of buildings.value) {
      const d = Math.hypot(b.latitude - lat, b.longitude - lng);
      if (d < minDist) {
        minDist = d;
        nearest = { code: b.code, name: b.name };
      }
    }
    return nearest;
  }

  return {
    activeFilter,
    activeTaskId,
    activeBuildingId,
    focusTaskId,
    pickerMode,
    pickedLat,
    pickedLng,
    pickedLabel,
    pickedBuildingCode,
    visiblePins,
    pinsWithDistance,
    categoryCounts,
    overviewStats,
    sidebarCollapsed,
    userLocation,
    nearbyOnly,
    activeTask,
    activeBuilding,
    buildings,
    tasksLoading,
    tasksError,
    setFilter,
    setFocus,
    showTask,
    clearTask,
    removeTask,
    openBuilding,
    closeBuilding,
    clearAll,
    enterPickerMode,
    leavePickerMode,
    pickPoint,
    fetchMapData,
    findNearestBuilding,
  };
});
