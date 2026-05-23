import apiClient from "@/api/client";
import type { RecommendationItem } from "@/types/api";

export async function listRecommendedTasks(): Promise<RecommendationItem[]> {
  const response = await apiClient.get("/api/recommendations/tasks");
  return response.data.data;
}
