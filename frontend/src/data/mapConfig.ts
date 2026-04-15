import type { MapConfig, FilterOption } from "@/types/map";

export const MAP_CONFIG: MapConfig = {
  center: [39.96003, 116.35097],
  campusBounds: [
    [39.95695, 116.34915],
    [39.96395, 116.35345],
  ],
  minZoom: 16,
  maxZoom: 20,
  maxNativeZoom: 19,
  initialZoom: 18,
  tileUrl: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
  tileAttribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
};

export const FILTERS: FilterOption[] = [
  { id: "all", label: "全部地图点位" },
  { id: "fast", label: "顺路极速单" },
  { id: "high", label: "高额悬赏" },
];
