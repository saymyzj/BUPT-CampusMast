import apiClient from "@/api/client";
import type { Notification, PaginationMeta } from "@/types/api";

export async function listNotifications(params?: {
  page?: number;
  limit?: number;
  unreadOnly?: boolean;
}): Promise<{ data: Notification[]; meta: PaginationMeta }> {
  const response = await apiClient.get("/api/notifications", { params });
  return { data: response.data.data, meta: response.data.meta };
}

export async function markNotificationRead(id: string): Promise<void> {
  await apiClient.patch(`/api/notifications/${id}/read`);
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiClient.patch("/api/notifications/read-all");
}
