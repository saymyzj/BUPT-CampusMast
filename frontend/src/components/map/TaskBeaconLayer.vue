<template>
  <div style="display: none"></div>
</template>

<script setup lang="ts">
import { watch, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import L from "leaflet";
import { useMapStore } from "@/stores/map";
import { useAuthStore } from "@/stores/auth";
import { useMapContext } from "@/composables/useLeafletMap";
import { acceptTask } from "@/api/modules/task";
import { CATEGORY_COLORS, type CategoryType } from "@/types/map";

const router = useRouter();
const { map, toLatLng } = useMapContext();
const mapStore = useMapStore();
const authStore = useAuthStore();
const layers: L.Layer[] = [];
const markerMap = new Map<string, L.Marker>();
let boundMap: L.Map | null = null;

function refreshMarkerPositions() {
  for (const marker of markerMap.values()) {
    marker.setLatLng(marker.getLatLng());
    (marker as any).update?.();
  }
}

function bindMapSync(m: L.Map) {
  if (boundMap === m) return;
  if (boundMap) {
    boundMap.off("zoom zoomend moveend viewreset resize", refreshMarkerPositions);
  }
  boundMap = m;
  m.on("zoom zoomend moveend viewreset resize", refreshMarkerPositions);
}

function escapeHtml(value: string | undefined | null) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function categorySvg(category: CategoryType | undefined) {
  const paths: Record<CategoryType, string> = {
    package: `
      <path d="M5 8.4 12 4l7 4.4v7.2L12 20l-7-4.4V8.4Z" />
      <path d="m5.4 8.6 6.6 4 6.6-4M12 12.6V20" />
    `,
    food: `
      <path d="M6 4v7M9 4v7M6 8.5h3M7.5 11v9" />
      <path d="M16 4c1.8 1.6 2.6 3.6 2.2 5.9-.3 1.8-1.3 3-2.7 3.6V20" />
    `,
    move: `
      <path d="M4 12h15M14 7l5 5-5 5" />
      <path d="M9 6H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h4" />
    `,
    other: `
      <path d="M12 3.8 14.2 9l5.5.5-4.2 3.6 1.3 5.4L12 15.6l-4.8 2.9 1.3-5.4-4.2-3.6 5.5-.5L12 3.8Z" />
    `,
  };
  return `
    <svg class="task-pin-svg" viewBox="0 0 24 24" aria-hidden="true">
      ${paths[category ?? "other"]}
    </svg>
  `;
}

function colorAlpha(hex: string, alphaHex: string) {
  return `${hex}${alphaHex}`;
}

function buildMarkerIcon(pinId: string) {
  const pin = mapStore.visiblePins.find((item) => item.id === pinId);
  const color = pin ? CATEGORY_COLORS[pin.category] : CATEGORY_COLORS.other;
  const icon = categorySvg(pin?.category);

  return L.divIcon({
    className: "task-pin-shell",
    html: `
      <span class="task-pin-pulse" style="border-color:${color}"></span>
      <span class="task-pin" style="background:${color}">
        <span class="task-pin-icon">${icon}</span>
      </span>
    `,
    iconSize: [38, 50],
    iconAnchor: [19, 43],
    popupAnchor: [0, -40],
  });
}

function buildPopupHtml(pinId: string) {
  const pin = mapStore.visiblePins.find((item) => item.id === pinId);
  if (!pin) return "";
  const color = CATEGORY_COLORS[pin.category];
  const requesterInitial = pin.requesterName.trim().charAt(0) || "?";
  const locationText = pin.to?.trim() || "校内地点";

  return `
    <div class="task-popup-card" data-task-popup="${escapeHtml(pin.id)}">
      <div class="task-popup-top">
        <span class="task-popup-tag" style="background:${colorAlpha(color, "18")};color:${color}">${escapeHtml(pin.label)}</span>
        <span class="task-popup-time">${escapeHtml(pin.timeLeft)}</span>
      </div>
      <div class="task-popup-heading">
        <h4 class="task-popup-title">${escapeHtml(pin.title)}</h4>
        <strong>${escapeHtml(pin.reward)}</strong>
      </div>
      <div class="task-popup-meta">
        <span class="task-popup-location">${escapeHtml(locationText)}</span>
      </div>
      <p class="task-popup-desc">${escapeHtml(pin.summary)}</p>
      <div class="task-popup-user">
        <span class="mini-avatar">${escapeHtml(requesterInitial)}</span>
        <span class="task-popup-name">${escapeHtml(pin.requesterName)}</span>
        <strong>信用分 ${escapeHtml(String(pin.requesterCreditScore))}</strong>
      </div>
      <div class="task-popup-actions">
        <button class="task-popup-btn secondary" data-detail-task="${escapeHtml(pin.id)}">查看详情</button>
        <button class="task-popup-btn primary" data-accept-task="${escapeHtml(pin.id)}">${escapeHtml(pin.action)}</button>
      </div>
    </div>
  `;
}

function openPopup(marker: L.Marker, pinId: string, syncStore = true) {
  marker.setIcon(buildMarkerIcon(pinId));
  marker.setPopupContent(buildPopupHtml(pinId));
  if (syncStore) mapStore.showTask(pinId);
  marker.openPopup();
}

function createMarkers(m: L.Map) {
  bindMapSync(m);
  clearLayers();

  for (const pin of mapStore.visiblePins) {
    const marker = L.marker(toLatLng(pin.position), {
      icon: buildMarkerIcon(pin.id),
      riseOnHover: true,
      keyboard: true,
      title: pin.title,
    }).addTo(m);

    marker.bindPopup(buildPopupHtml(pin.id), {
      closeButton: false,
      autoPan: false,
      keepInView: false,
      maxWidth: 320,
      className: "task-popup-shell",
    });

    marker.on("click", (e) => {
      L.DomEvent.stopPropagation(e);
      openPopup(marker, pin.id);
    });

    marker.on("mouseover", () => mapStore.setFocus(pin.id));
    marker.on("mouseout", () => mapStore.setFocus(null));
    marker.on("popupclose", () => {
      if (mapStore.activeTaskId === pin.id) mapStore.clearTask();
    });
    marker.on("popupopen", (event) => {
      const popupEl = event.popup.getElement();
      if (!popupEl || (popupEl as any).__delegated) return;
      (popupEl as any).__delegated = true;
      popupEl.addEventListener("click", async (e: Event) => {
        const target = e.target as HTMLElement;
        const detailBtn = target.closest("[data-detail-task]") as HTMLElement | null;
        if (detailBtn) {
          e.stopPropagation();
          router.push(`/tasks/${detailBtn.dataset.detailTask ?? pin.id}`);
          return;
        }

        const acceptBtn = target.closest("[data-accept-task]") as HTMLButtonElement | null;
        if (!acceptBtn) return;
        e.stopPropagation();
        const taskId = acceptBtn.dataset.acceptTask ?? "";
        if (!authStore.isAuthenticated) {
          marker.closePopup();
          router.push("/login");
          return;
        }
        acceptBtn.textContent = "接单中...";
        acceptBtn.disabled = true;
        try {
          await acceptTask(taskId);
          marker.closePopup();
          mapStore.removeTask(taskId);
          mapStore.clearTask();
          alert("接单成功，可在“我的任务”中查看进度。");
        } catch (err: any) {
          const msg = err?.response?.data?.error?.message || "请重试";
          alert(`接单失败：${msg}`);
          acceptBtn.textContent = "接单";
          acceptBtn.disabled = false;
        }
      });
    });

    markerMap.set(pin.id, marker);
    layers.push(marker);
  }
}

function clearLayers() {
  layers.forEach((layer) => layer.remove());
  layers.length = 0;
  markerMap.clear();
}

watch(
  [map, () => mapStore.visiblePins],
  ([m]) => {
    if (m) createMarkers(m);
  },
  { immediate: true },
);

watch(
  () => mapStore.focusTaskId,
  (id) => {
    for (const [pinId, marker] of markerMap) {
      const el = marker.getElement();
      if (el) el.classList.toggle("is-focused", pinId === id);
    }
  },
);

watch(
  () => mapStore.activeTaskId,
  (id, prevId) => {
    if (prevId && prevId !== id) markerMap.get(prevId)?.closePopup();
    if (!id) return;
    const marker = markerMap.get(id);
    if (!marker) return;
    if (marker.getPopup()?.isOpen()) return;
    openPopup(marker, id, false);
  },
);

onMounted(() => {
  mapStore.fetchMapData();
});

onUnmounted(() => {
  if (boundMap) {
    boundMap.off("zoom zoomend moveend viewreset resize", refreshMarkerPositions);
    boundMap = null;
  }
  clearLayers();
});
</script>

<style>
.task-pin-shell {
  background: transparent;
  border: none;
}

.task-pin-pulse {
  position: absolute;
  left: 4px;
  top: 4px;
  width: 30px;
  height: 30px;
  border: 2px dashed;
  border-radius: 50%;
  opacity: 0;
}

.task-pin {
  position: absolute;
  left: 4px;
  top: 0;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 3px solid #fff;
  border-radius: 50% 50% 50% 7px;
  box-shadow: 0 10px 22px rgba(31, 36, 48, 0.22);
  transform: rotate(-45deg);
}

.task-pin::after {
  content: "";
  position: absolute;
  left: 6px;
  bottom: -10px;
  width: 14px;
  height: 6px;
  border-radius: 50%;
  background: rgba(31, 36, 48, 0.2);
  filter: blur(2px);
  transform: rotate(45deg);
}

.task-pin-icon {
  transform: rotate(45deg);
  color: #fff;
  line-height: 1;
}

.task-pin-svg {
  width: 15px;
  height: 15px;
  display: block;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.task-pin-shell.is-focused .task-pin,
.task-pin-shell:hover .task-pin {
  transform: rotate(-45deg) scale(1.12);
}

.task-pin-shell.is-focused .task-pin-pulse,
.task-pin-shell:hover .task-pin-pulse {
  animation: task-pin-pulse 1.4s ease-out infinite;
}

@keyframes task-pin-pulse {
  0% { opacity: 0.58; transform: scale(0.76); }
  100% { opacity: 0; transform: scale(1.9); }
}

.task-popup-shell .leaflet-popup-content-wrapper {
  overflow: hidden;
  border: 1px solid #ece8df;
  border-radius: 14px;
  background: #fffdfa;
  box-shadow: 0 18px 38px rgba(65, 57, 46, 0.14);
}

.task-popup-shell .leaflet-popup-content {
  margin: 0;
}

.task-popup-shell .leaflet-popup-tip {
  background: #fffdfa;
  box-shadow: 0 8px 18px rgba(65, 57, 46, 0.1);
}

.task-popup-card {
  width: 286px;
  padding: 16px;
  color: #252723;
  font-family: "Inter", "Noto Sans SC", "Microsoft YaHei", sans-serif;
}

.task-popup-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 9px;
}

.task-popup-tag {
  padding: 4px 9px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 850;
}

.task-popup-time {
  color: #85877f;
  font-size: 12px;
  font-weight: 700;
}

.task-popup-heading {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: 12px;
  margin-bottom: 8px;
}

.task-popup-title {
  margin: 0;
  min-width: 0;
  overflow: hidden;
  color: #191b17;
  font-size: 16px;
  font-weight: 950;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-popup-heading strong {
  color: #6f835f;
  font-size: 18px;
  font-weight: 950;
  white-space: nowrap;
}

.task-popup-meta {
  display: block;
  margin-bottom: 10px;
  padding-right: 76px;
}

.task-popup-location {
  min-width: 0;
  display: -webkit-box;
  overflow: hidden;
  color: #83857e;
  font-size: 12px;
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: normal;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.task-popup-desc {
  margin: 0 0 12px;
  color: #74766f;
  font-size: 12px;
  line-height: 1.55;
}

.task-popup-user {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  color: #74766f;
  font-size: 12px;
  font-weight: 700;
  min-width: 0;
}

.task-popup-user strong {
  color: #df8a2f;
  white-space: nowrap;
}

.task-popup-name {
  min-width: 0;
  overflow: hidden;
  color: #2d2f2a;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mini-avatar {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #596d4b;
  background: #e5d9cb;
  font-weight: 900;
}

.task-popup-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.task-popup-btn {
  height: 38px;
  border: 1px solid transparent;
  border-radius: 9px;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  font-weight: 900;
}

.task-popup-btn.primary {
  color: #fff;
  background: #6f835f;
  box-shadow: 0 10px 22px rgba(91, 111, 76, 0.18);
}

.task-popup-btn.secondary {
  color: #4e514a;
  background: #f6f4ef;
  border-color: #e8e4dc;
}
</style>
