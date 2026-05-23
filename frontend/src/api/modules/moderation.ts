import apiClient from "@/api/client";
import type { ModerationRecord } from "@/types/api";

export async function listMyModerationRecords(): Promise<ModerationRecord[]> {
  const response = await apiClient.get("/api/moderation/my-records");
  return response.data.data;
}
