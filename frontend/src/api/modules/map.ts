import apiClient from "@/api/client";
import type { CampusBuilding, NearbyTask } from "@/types/api";

export async function listCampusBuildings(): Promise<CampusBuilding[]> {
  const response = await apiClient.get("/api/map/buildings");
  return response.data.data;
}

export async function listNearbyTasks(params: {
  buildingCode: string;
  limit?: number;
}): Promise<NearbyTask[]> {
  const response = await apiClient.get("/api/map/tasks/nearby", { params });
  return response.data.data;
}
