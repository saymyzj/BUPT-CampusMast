export type BuildingType =
  | "teaching"
  | "teaching2"
  | "dorm"
  | "canteen"
  | "library"
  | "research"
  | "admin"
  | "service"
  | "sports"
  | "green"
  | "residential"
  | "logistics";

export type CategoryType = "package" | "food" | "move" | "other";
export type FilterType = "all" | "fast" | "high";
export type LatLngTuple = [number, number];

export interface FloorPoi {
  name: string;
  desc: string;
  color: string;
}

export interface BuildingFloor {
  id: string;
  name: string;
  summary: string;
  highlights: string[];
  pois: FloorPoi[];
}

export interface Building {
  id: string;
  name: string;
  abbr: string;
  type: BuildingType;
  core: boolean;
  center: LatLngTuple;
  polygon?: LatLngTuple[];
  summary: string;
  floors?: BuildingFloor[];
}

export interface TaskPin {
  id: string;
  buildingId: string;
  category: CategoryType;
  filter: FilterType;
  reward: string;
  timeLeft: string;
  title: string;
  summary: string;
  shortLabel: string;
  position: LatLngTuple;
  room: string;
  label: string;
  action: string;
}

export interface MapConfig {
  center: LatLngTuple;
  campusBounds: [LatLngTuple, LatLngTuple];
  minZoom: number;
  maxZoom: number;
  maxNativeZoom: number;
  initialZoom: number;
  tileUrl: string;
  tileAttribution: string;
}

export interface FilterOption {
  id: FilterType;
  label: string;
}

export const CATEGORY_COLORS: Record<CategoryType, string> = {
  package: "#4d83c8",
  food: "#f1892d",
  move: "#52b478",
  other: "#8b75d7",
};

export const CATEGORY_LABELS: Record<CategoryType, string> = {
  package: "代取快递",
  food: "代买餐食",
  move: "搬运重物",
  other: "其他",
};

export const CATEGORY_ICONS: Record<CategoryType, string> = {
  package: "📦",
  food: "🍱",
  move: "📦",
  other: "🔧",
};
