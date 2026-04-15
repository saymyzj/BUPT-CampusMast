<template>
  <div style="display: none"></div>
</template>

<script setup lang="ts">
import { watch, onUnmounted } from "vue";
import L from "leaflet";
import { buildings } from "@/data/buildings";
import { useMapStore } from "@/stores/map";
import { useMapContext } from "@/composables/useLeafletMap";
import { CATEGORY_COLORS } from "@/types/map";

type PopupPlacement =
  | "top"
  | "top-right"
  | "right"
  | "bottom-right"
  | "bottom"
  | "bottom-left"
  | "left"
  | "top-left";

const { map, toLatLng } = useMapContext();
const mapStore = useMapStore();
const layers: L.Layer[] = [];
let hoverCloseTimer: number | null = null;
const POPUP_VIEWPORT_PADDING = 18;
const POPUP_ANCHOR_GAP = 20;
const POPUP_TIP_SIZE = 14;

function clearHoverTimer() {
  if (hoverCloseTimer !== null) {
    window.clearTimeout(hoverCloseTimer);
    hoverCloseTimer = null;
  }
}

function buildPopupHtml(pinId: string) {
  const pin = mapStore.visiblePins.find((item) => item.id === pinId);
  const building = buildings.find((item) => item.id === pin?.buildingId);
  if (!pin) return "";
  const color = CATEGORY_COLORS[pin.category];
  const urgent = pin.timeLeft.includes("分钟") || pin.timeLeft.includes("马上");

  return `
    <div class="task-popup-card" data-task-popup="${pin.id}">
      <div class="task-popup-top">
        <span class="task-popup-tag" style="background:${color}18;color:${color}">${pin.label}</span>
        <span class="task-popup-time ${urgent ? "urgent" : ""}">${pin.timeLeft}</span>
      </div>
      <div class="task-popup-reward" style="color:${color}">${pin.reward}</div>
      <h4 class="task-popup-title">${pin.title}</h4>
      <p class="task-popup-desc">${pin.summary}</p>
      <div class="task-popup-meta">
        <span class="task-popup-pill">${building?.name ?? "楼宇"} · ${pin.room}</span>
      </div>
      <div class="task-popup-actions">
        <button class="task-popup-btn primary" data-open-building="${pin.buildingId}">${pin.action}</button>
        <button class="task-popup-btn secondary" data-close-popup="${pin.id}">关闭</button>
      </div>
    </div>
  `;
}

function setPopupPlacementClass(popupEl: HTMLElement, placement: PopupPlacement) {
  popupEl.classList.remove(
    "is-top",
    "is-top-right",
    "is-right",
    "is-bottom-right",
    "is-bottom",
    "is-bottom-left",
    "is-left",
    "is-top-left",
  );
  popupEl.classList.add(`is-${placement}`);
}

function getPlacementRect(point: L.Point, width: number, height: number, placement: PopupPlacement) {
  switch (placement) {
    case "top":
      return { left: point.x - width / 2, top: point.y - height - POPUP_ANCHOR_GAP };
    case "top-right":
      return { left: point.x + POPUP_ANCHOR_GAP, top: point.y - height - POPUP_ANCHOR_GAP };
    case "right":
      return { left: point.x + POPUP_ANCHOR_GAP, top: point.y - height / 2 };
    case "bottom-right":
      return { left: point.x + POPUP_ANCHOR_GAP, top: point.y + POPUP_ANCHOR_GAP };
    case "bottom":
      return { left: point.x - width / 2, top: point.y + POPUP_ANCHOR_GAP };
    case "bottom-left":
      return { left: point.x - width - POPUP_ANCHOR_GAP, top: point.y + POPUP_ANCHOR_GAP };
    case "left":
      return { left: point.x - width - POPUP_ANCHOR_GAP, top: point.y - height / 2 };
    case "top-left":
    default:
      return { left: point.x - width - POPUP_ANCHOR_GAP, top: point.y - height - POPUP_ANCHOR_GAP };
  }
}

function choosePopupPlacement(m: L.Map, layer: L.CircleMarker, popupEl: HTMLElement): PopupPlacement {
  const point = m.latLngToContainerPoint(layer.getLatLng());
  const size = m.getSize();
  const width = popupEl.offsetWidth;
  const height = popupEl.offsetHeight;
  const requiredWidth = width + POPUP_ANCHOR_GAP + POPUP_TIP_SIZE + POPUP_VIEWPORT_PADDING;
  const requiredHeight = height + POPUP_ANCHOR_GAP + POPUP_TIP_SIZE + POPUP_VIEWPORT_PADDING;
  const nearLeft = point.x < requiredWidth;
  const nearRight = size.x - point.x < requiredWidth;
  const nearTop = point.y < requiredHeight;
  const nearBottom = size.y - point.y < requiredHeight;

  let preferredPlacements: PopupPlacement[];

  if (nearLeft && nearTop) {
    preferredPlacements = ["bottom-right", "right", "bottom", "top-right", "bottom-left", "top", "left", "top-left"];
  } else if (nearRight && nearTop) {
    preferredPlacements = ["bottom-left", "left", "bottom", "top-left", "bottom-right", "top", "right", "top-right"];
  } else if (nearRight && nearBottom) {
    preferredPlacements = ["top-left", "left", "top", "bottom-left", "top-right", "bottom", "right", "bottom-right"];
  } else if (nearLeft && nearBottom) {
    preferredPlacements = ["top-right", "right", "top", "bottom-right", "top-left", "bottom", "left", "bottom-left"];
  } else if (nearTop) {
    preferredPlacements = ["bottom", "bottom-right", "bottom-left", "right", "left", "top", "top-right", "top-left"];
  } else if (nearBottom) {
    preferredPlacements = ["top", "top-right", "top-left", "right", "left", "bottom", "bottom-right", "bottom-left"];
  } else if (nearLeft) {
    preferredPlacements = ["right", "top-right", "bottom-right", "top", "bottom", "left", "top-left", "bottom-left"];
  } else if (nearRight) {
    preferredPlacements = ["left", "top-left", "bottom-left", "top", "bottom", "right", "top-right", "bottom-right"];
  } else {
    preferredPlacements = ["top", "top-right", "top-left", "right", "left", "bottom", "bottom-right", "bottom-left"];
  }

  const fitsPlacement = (placement: PopupPlacement) => {
    const rect = getPlacementRect(point, width, height, placement);
    return (
      rect.left >= POPUP_VIEWPORT_PADDING &&
      rect.top >= POPUP_VIEWPORT_PADDING &&
      rect.left + width <= size.x - POPUP_VIEWPORT_PADDING &&
      rect.top + height <= size.y - POPUP_VIEWPORT_PADDING
    );
  };

  const firstFit = preferredPlacements.find(fitsPlacement);
  if (firstFit) return firstFit;

  return preferredPlacements.reduce((bestPlacement, placement) => {
    const rect = getPlacementRect(point, width, height, placement);
    const overflow =
      Math.max(POPUP_VIEWPORT_PADDING - rect.left, 0) +
      Math.max(POPUP_VIEWPORT_PADDING - rect.top, 0) +
      Math.max(rect.left + width - (size.x - POPUP_VIEWPORT_PADDING), 0) +
      Math.max(rect.top + height - (size.y - POPUP_VIEWPORT_PADDING), 0);

    const bestRect = getPlacementRect(point, width, height, bestPlacement);
    const bestOverflow =
      Math.max(POPUP_VIEWPORT_PADDING - bestRect.left, 0) +
      Math.max(POPUP_VIEWPORT_PADDING - bestRect.top, 0) +
      Math.max(bestRect.left + width - (size.x - POPUP_VIEWPORT_PADDING), 0) +
      Math.max(bestRect.top + height - (size.y - POPUP_VIEWPORT_PADDING), 0);

    return overflow < bestOverflow ? placement : bestPlacement;
  }, preferredPlacements[0]);
}

function getPopupOffset(placement: PopupPlacement, popupEl: HTMLElement) {
  const width = popupEl.offsetWidth;
  const height = popupEl.offsetHeight;
  const sideOffset = width / 2 + POPUP_ANCHOR_GAP;
  const verticalOffset = height + POPUP_ANCHOR_GAP;

  switch (placement) {
    case "top-right":
      return L.point(sideOffset, -POPUP_ANCHOR_GAP);
    case "right":
      return L.point(sideOffset, 0);
    case "bottom-right":
      return L.point(sideOffset, verticalOffset);
    case "bottom-left":
      return L.point(-sideOffset, verticalOffset);
    case "left":
      return L.point(-sideOffset, 0);
    case "top-left":
      return L.point(-sideOffset, -POPUP_ANCHOR_GAP);
    case "bottom":
      return L.point(0, verticalOffset);
    case "top":
    default:
      return L.point(0, -POPUP_ANCHOR_GAP);
  }
}

function syncPopupPlacement(m: L.Map, layer: L.CircleMarker) {
  const popup = layer.getPopup();
  const popupEl = popup?.getElement();
  if (!popup || !popupEl) return;

  const placement = choosePopupPlacement(m, layer, popupEl);
  popup.options.offset = getPopupOffset(placement, popupEl);
  setPopupPlacementClass(popupEl, placement);
  popup.update();
}

function scheduleClose(layer: L.CircleMarker) {
  clearHoverTimer();
  hoverCloseTimer = window.setTimeout(() => {
    layer.closePopup();
    mapStore.clearTask();
  }, 180);
}

function openAdaptivePopup(m: L.Map, layer: L.CircleMarker, pinId: string) {
  clearHoverTimer();
  const popup = layer.getPopup();
  if (!popup) return;
  popup.setContent(buildPopupHtml(pinId));
  popup.options.offset = L.point(0, -POPUP_ANCHOR_GAP);
  mapStore.showTask(pinId);
  layer.openPopup();
  window.requestAnimationFrame(() => syncPopupPlacement(m, layer));
}

function createMarkers(m: L.Map) {
  clearLayers();

  for (const pin of mapStore.visiblePins) {
    const color = CATEGORY_COLORS[pin.category];
    const latlng = toLatLng(pin.position);

    const pulse = L.circleMarker(latlng, {
      radius: 18,
      color,
      weight: 2,
      opacity: 0.32,
      fillOpacity: 0,
      interactive: false,
      className: "task-pulse-circle",
    }).addTo(m);

    const core = L.circleMarker(latlng, {
      radius: 7,
      color: "#ffffff",
      weight: 2.5,
      fillColor: color,
      fillOpacity: 1,
      bubblingMouseEvents: false,
      className: "task-core-circle",
    }).addTo(m);

    core.bindTooltip(pin.shortLabel, {
      permanent: true,
      direction: "right",
      offset: L.point(10, 0),
      className: "task-summary-tooltip",
      opacity: 1,
      interactive: false,
    });

    core.bindPopup(buildPopupHtml(pin.id), {
      closeButton: false,
      autoPan: false,
      keepInView: false,
      offset: L.point(18, -18),
      className: "task-popup-shell",
    });

    core.on("mouseover", () => openAdaptivePopup(m, core, pin.id));
    core.on("click", (e) => {
      L.DomEvent.stopPropagation(e);
      openAdaptivePopup(m, core, pin.id);
    });
    core.on("mouseout", () => scheduleClose(core));

    core.on("popupopen", (event) => {
      const popupEl = event.popup.getElement();
      if (!popupEl) return;

      syncPopupPlacement(m, core);

      popupEl.addEventListener("mouseenter", clearHoverTimer);
      popupEl.addEventListener("mouseleave", () => scheduleClose(core));

      popupEl.querySelectorAll<HTMLElement>("[data-open-building]").forEach((btn) => {
        btn.onclick = () => {
          mapStore.openBuilding(btn.dataset.openBuilding ?? "");
          core.closePopup();
        };
      });

      popupEl.querySelectorAll<HTMLElement>("[data-close-popup]").forEach((btn) => {
        btn.onclick = () => {
          core.closePopup();
          mapStore.clearTask();
        };
      });
    });

    m.on("zoomend moveend", () => {
      if (core.isPopupOpen()) {
        openAdaptivePopup(m, core, pin.id);
      }
    });

    layers.push(pulse, core);
  }
}

function clearLayers() {
  layers.forEach((layer) => layer.remove());
  layers.length = 0;
}

watch(
  [map, () => mapStore.visiblePins],
  ([m]) => {
    if (m) createMarkers(m);
  },
  { immediate: true }
);

onUnmounted(() => {
  clearLayers();
  clearHoverTimer();
});
</script>

<style>
.task-core-circle {
  filter: drop-shadow(0 8px 16px rgba(17, 20, 27, 0.22));
}

.task-pulse-circle {
  animation: beacon-pulse-ring 2.4s ease-out infinite;
  transform-origin: center;
}

@keyframes beacon-pulse-ring {
  0% { transform: scale(0.88); opacity: 0.28; }
  70% { transform: scale(1.7); opacity: 0; }
  100% { transform: scale(1.7); opacity: 0; }
}

.task-summary-tooltip {
  background: transparent;
  border: none;
  box-shadow: none;
}

.task-summary-tooltip .leaflet-tooltip-content {
  margin: 0;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(255, 251, 245, 0.92);
  border: 1px solid rgba(31, 42, 58, 0.1);
  box-shadow: 0 8px 16px rgba(31, 34, 48, 0.1);
  font-family: "Fredoka", "Noto Sans SC", sans-serif;
  font-size: 11px;
  font-weight: 700;
  color: #1f2230;
  max-width: 58px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-summary-tooltip::before {
  display: none;
}

.task-popup-shell .leaflet-popup-content-wrapper {
  border-radius: 20px;
  background: rgba(248, 243, 235, 0.98);
  border: 1px solid rgba(31, 42, 58, 0.08);
  box-shadow: 0 22px 42px rgba(31, 34, 48, 0.18);
  overflow: visible;
}

.task-popup-shell .leaflet-popup-content {
  margin: 0;
}

.task-popup-shell {
  margin-bottom: 0;
}

.task-popup-shell,
.task-popup-shell.leaflet-zoom-animated,
.leaflet-fade-anim .task-popup-shell,
.leaflet-zoom-anim .task-popup-shell.leaflet-zoom-animated,
.task-popup-shell .leaflet-popup-content-wrapper,
.task-popup-shell .leaflet-popup-tip,
.task-popup-shell .leaflet-popup-tip-container {
  transition: none !important;
  animation: none !important;
}

.task-popup-shell .leaflet-popup-tip-container {
  position: absolute;
  margin: 0;
  overflow: visible;
  pointer-events: none;
}

.task-popup-shell .leaflet-popup-tip {
  margin: 0;
  width: 24px;
  height: 14px;
  background: rgba(248, 243, 235, 0.98);
  box-shadow: none;
  transform: none;
  filter: drop-shadow(0 6px 10px rgba(31, 34, 48, 0.08));
}

.task-popup-shell.is-top .leaflet-popup-tip-container {
  width: 24px;
  height: 14px;
  left: 50%;
  bottom: -13px;
  transform: translateX(-50%);
}

.task-popup-shell.is-top .leaflet-popup-tip {
  clip-path: polygon(0 0, 100% 0, 50% 100%);
}

.task-popup-shell.is-bottom .leaflet-popup-tip-container {
  width: 24px;
  height: 14px;
  left: 50%;
  top: -13px;
  transform: translateX(-50%);
}

.task-popup-shell.is-bottom .leaflet-popup-tip {
  clip-path: polygon(50% 0, 0 100%, 100% 100%);
}

.task-popup-shell.is-left .leaflet-popup-tip-container {
  width: 14px;
  height: 24px;
  right: -13px;
  top: 50%;
  transform: translateY(-50%);
}

.task-popup-shell.is-left .leaflet-popup-tip {
  width: 14px;
  height: 24px;
  clip-path: polygon(0 0, 100% 50%, 0 100%);
}

.task-popup-shell.is-right .leaflet-popup-tip-container {
  width: 14px;
  height: 24px;
  left: -13px;
  top: 50%;
  transform: translateY(-50%);
}

.task-popup-shell.is-right .leaflet-popup-tip {
  width: 14px;
  height: 24px;
  clip-path: polygon(100% 0, 0 50%, 100% 100%);
}

.task-popup-shell.is-bottom-right .leaflet-popup-tip-container,
.task-popup-shell.is-bottom-left .leaflet-popup-tip-container,
.task-popup-shell.is-top-right .leaflet-popup-tip-container,
.task-popup-shell.is-top-left .leaflet-popup-tip-container {
  width: 18px;
  height: 18px;
}

.task-popup-shell.is-bottom-right .leaflet-popup-tip,
.task-popup-shell.is-bottom-left .leaflet-popup-tip,
.task-popup-shell.is-top-right .leaflet-popup-tip,
.task-popup-shell.is-top-left .leaflet-popup-tip {
  width: 18px;
  height: 18px;
}

.task-popup-shell.is-bottom-right .leaflet-popup-tip-container {
  left: 14px;
  top: -17px;
}

.task-popup-shell.is-bottom-right .leaflet-popup-tip {
  clip-path: polygon(0 0, 100% 100%, 0 100%);
}

.task-popup-shell.is-bottom-left .leaflet-popup-tip-container {
  right: 14px;
  top: -17px;
}

.task-popup-shell.is-bottom-left .leaflet-popup-tip {
  clip-path: polygon(100% 0, 100% 100%, 0 100%);
}

.task-popup-shell.is-top-right .leaflet-popup-tip-container {
  left: 14px;
  bottom: -17px;
}

.task-popup-shell.is-top-right .leaflet-popup-tip {
  clip-path: polygon(0 0, 100% 0, 0 100%);
}

.task-popup-shell.is-top-left .leaflet-popup-tip-container {
  right: 14px;
  bottom: -17px;
}

.task-popup-shell.is-top-left .leaflet-popup-tip {
  clip-path: polygon(100% 0, 100% 100%, 0 0);
}

.task-popup-card {
  width: 292px;
  padding: 16px;
  font-family: "Noto Sans SC", sans-serif;
  color: #1f2230;
}

.task-popup-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.task-popup-tag {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
}

.task-popup-time {
  font-size: 11px;
  color: #748399;
  font-weight: 700;
}

.task-popup-time.urgent {
  color: #d96c53;
}

.task-popup-reward {
  font-family: "Fredoka", "Noto Sans SC", sans-serif;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 8px;
}

.task-popup-title {
  font-size: 17px;
  font-weight: 800;
  line-height: 1.35;
  margin-bottom: 8px;
}

.task-popup-desc {
  font-size: 13px;
  line-height: 1.6;
  color: #6d7888;
  margin-bottom: 12px;
}

.task-popup-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.task-popup-pill {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(31, 34, 48, 0.06);
  font-size: 11px;
  font-weight: 700;
  color: #405068;
}

.task-popup-actions {
  display: flex;
  gap: 8px;
}

.task-popup-btn {
  flex: 1;
  border: none;
  border-radius: 14px;
  padding: 11px 12px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 800;
  transition: 160ms ease;
}

.task-popup-btn.primary {
  background: #1f2230;
  color: #fff;
}

.task-popup-btn.secondary {
  background: rgba(31, 34, 48, 0.06);
  color: #1f2230;
}
</style>
