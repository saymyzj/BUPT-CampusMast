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
import { CATEGORY_COLORS, CATEGORY_ICONS } from "@/types/map";

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

function buildMarkerIcon(pinId: string) {
  const pin = mapStore.visiblePins.find((item) => item.id === pinId);
  const color = pin ? CATEGORY_COLORS[pin.category] : "#7c4dff";
  const icon = pin ? CATEGORY_ICONS[pin.category] : "•";

  return L.divIcon({
    className: "task-pin-shell",
    html: `
      <span class="task-pin-pulse" style="border-color:${color}"></span>
      <span class="task-pin" style="background:${color}">
        <span class="task-pin-icon">${icon}</span>
      </span>
    `,
    iconSize: [46, 58],
    iconAnchor: [23, 50],
    popupAnchor: [0, -48],
  });
}

function buildPopupHtml(pinId: string) {
  const pin = mapStore.visiblePins.find((item) => item.id === pinId);
  if (!pin) return "";
  const color = CATEGORY_COLORS[pin.category];
  const requesterInitial = pin.requesterName.trim().charAt(0) || "?";

  return `
    <div class="task-popup-card" data-task-popup="${escapeHtml(pin.id)}">
      <div class="task-popup-top">
        <span class="task-popup-tag" style="background:${color}18;color:${color}">${escapeHtml(pin.label)}</span>
        <span class="task-popup-time">剩余 ${escapeHtml(pin.timeLeft)}</span>
      </div>
      <h4 class="task-popup-title">${escapeHtml(pin.title)}</h4>
      <div class="task-popup-reward">${escapeHtml(pin.reward)}</div>
      <p class="task-popup-desc">${escapeHtml(pin.summary)}</p>
      <div class="task-popup-user">
        <span class="mini-avatar">${escapeHtml(requesterInitial)}</span>
        <span>${escapeHtml(pin.requesterName)}</span>
        <strong>信用 ${escapeHtml(String(pin.requesterCreditScore))}</strong>
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
    marker.on("popupclose", () => mapStore.clearTask());
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
  left: 5px;
  top: 5px;
  width: 36px;
  height: 36px;
  border: 2px dashed;
  border-radius: 50%;
  opacity: 0;
}

.task-pin {
  position: absolute;
  left: 5px;
  top: 0;
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border: 4px solid #fff;
  border-radius: 50% 50% 50% 8px;
  box-shadow: 0 12px 26px rgba(31, 36, 48, 0.25);
  transform: rotate(-45deg);
}

.task-pin::after {
  content: "";
  position: absolute;
  left: 7px;
  bottom: -13px;
  width: 17px;
  height: 7px;
  border-radius: 50%;
  background: rgba(31, 36, 48, 0.2);
  filter: blur(2px);
  transform: rotate(45deg);
}

.task-pin-icon {
  transform: rotate(45deg);
  color: #fff;
  font-size: 18px;
  line-height: 1;
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
  border: 1px solid rgba(31, 36, 48, 0.07);
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 22px 60px rgba(31, 36, 48, 0.18);
}

.task-popup-shell .leaflet-popup-content {
  margin: 0;
}

.task-popup-shell .leaflet-popup-tip {
  background: #fff;
  box-shadow: 0 8px 20px rgba(31, 36, 48, 0.12);
}

.task-popup-card {
  width: 300px;
  padding: 18px;
  color: #202633;
  font-family: "Noto Sans SC", "Microsoft YaHei", sans-serif;
}

.task-popup-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.task-popup-tag {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
}

.task-popup-time {
  color: #8b93a2;
  font-size: 12px;
  font-weight: 800;
}

.task-popup-title {
  margin: 0 0 8px;
  color: #111827;
  font-size: 17px;
  font-weight: 900;
  line-height: 1.35;
}

.task-popup-reward {
  margin-bottom: 10px;
  color: #f17b2f;
  font-family: "Fredoka", "Noto Sans SC", sans-serif;
  font-size: 24px;
  font-weight: 900;
}

.task-popup-desc {
  margin: 0 0 12px;
  color: #7d8494;
  font-size: 12px;
  line-height: 1.55;
}

.task-popup-user {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  color: #6d7482;
  font-size: 12px;
  font-weight: 700;
}

.task-popup-user strong {
  color: #f0ad1e;
}

.mini-avatar {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: #111827;
}

.task-popup-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.task-popup-btn {
  height: 42px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  font-weight: 900;
}

.task-popup-btn.primary {
  color: #fff;
  background: linear-gradient(135deg, #8657ff, #596cff);
  box-shadow: 0 12px 22px rgba(108, 92, 231, 0.25);
}

.task-popup-btn.secondary {
  color: #3a4050;
  background: #f6f7fa;
  border: 1px solid #eceef3;
}
</style>
