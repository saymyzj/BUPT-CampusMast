import { ref, onMounted, onUnmounted, provide, inject, type Ref, type InjectionKey } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { MAP_CONFIG } from "@/data/mapConfig";
import type { LatLngTuple } from "@/types/map";

export interface MapContext {
  map: Ref<L.Map | null>;
  toLatLng: (point: LatLngTuple) => L.LatLng;
  projectToViewport: (point: LatLngTuple) => { x: number; y: number } | null;
}

const MAP_KEY: InjectionKey<MapContext> = Symbol("leaflet-map");
const DRAG_PADDING_RATIO = 0.22;

function expandBoundsForViewport(m: L.Map, bounds: L.LatLngBounds) {
  const zoom = m.getZoom();
  const halfViewport = m.getSize().divideBy(2);
  const northWest = m.project(bounds.getNorthWest(), zoom);
  const southEast = m.project(bounds.getSouthEast(), zoom);
  const pixelBounds = L.bounds(northWest, southEast);
  const pixelMin = pixelBounds.min!;
  const pixelMax = pixelBounds.max!;

  const expandedPixelBounds = L.bounds(
    pixelMin.subtract(halfViewport),
    pixelMax.add(halfViewport),
  );
  const expandedMin = expandedPixelBounds.min!;
  const expandedMax = expandedPixelBounds.max!;

  return L.latLngBounds(
    m.unproject(expandedMin, zoom),
    m.unproject(expandedMax, zoom),
  );
}

export function provideLeafletMap(containerRef: Ref<HTMLElement | null>) {
  const map: Ref<L.Map | null> = ref(null);
  function toLatLng(point: LatLngTuple): L.LatLng {
    return L.latLng(point[0], point[1]);
  }

  function projectToViewport(point: LatLngTuple): { x: number; y: number } | null {
    if (!map.value) return null;
    const projected = map.value.latLngToContainerPoint(toLatLng(point));
    const mapEl = map.value.getContainer();
    const rect = mapEl.getBoundingClientRect();
    return {
      x: rect.left + projected.x,
      y: rect.top + projected.y,
    };
  }

  onMounted(() => {
    if (!containerRef.value) return;

    const campusBounds = L.latLngBounds(MAP_CONFIG.campusBounds);
    const dragCenterBounds = campusBounds.pad(DRAG_PADDING_RATIO);

    const m = L.map(containerRef.value, {
      minZoom: MAP_CONFIG.minZoom,
      maxZoom: MAP_CONFIG.maxZoom,
      maxBoundsViscosity: 0.45,
      zoomSnap: 0.25,
      zoomDelta: 0.5,
      attributionControl: true,
      zoomControl: false,
    });

    L.tileLayer(MAP_CONFIG.tileUrl, {
      attribution: MAP_CONFIG.tileAttribution,
      maxZoom: MAP_CONFIG.maxZoom,
      maxNativeZoom: MAP_CONFIG.maxNativeZoom,
    }).addTo(m);

    const syncDragBounds = () => {
      m.setMaxBounds(expandBoundsForViewport(m, dragCenterBounds));
    };

    m.fitBounds(campusBounds, { padding: [16, 16] });
    syncDragBounds();
    m.on("zoomend resize", syncDragBounds);
    L.control.zoom({ position: "bottomright" }).addTo(m);

    map.value = m;
  });

  onUnmounted(() => {
    map.value?.remove();
    map.value = null;
  });

  const ctx: MapContext = { map, toLatLng, projectToViewport };
  provide(MAP_KEY, ctx);

  return ctx;
}

export function useMapContext(): MapContext {
  const ctx = inject(MAP_KEY);
  if (!ctx) throw new Error("useMapContext must be used inside a MapContainer");
  return ctx;
}
