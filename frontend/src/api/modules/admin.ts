import apiClient from "@/api/client";
import type {
  User,
  Task,
  ModerationRecord,
  ConfigItem,
  HomepageBlock,
  AdminUpdateUserRequest,
  AdminResolveDisputeRequest,
  AdminReviewModerationRequest,
  AdminUpdateConfigRequest,
  HomepageBlockUpsert,
  PaginationMeta,
  ModerationResult,
  AdminReviewStatus,
} from "@/types/api";

// ===== 用户管理 =====
export async function adminListUsers(params?: {
  page?: number;
  limit?: number;
  keyword?: string;
}): Promise<{ data: User[]; meta: PaginationMeta }> {
  const response = await apiClient.get("/api/admin/users", { params });
  return { data: response.data.data, meta: response.data.meta };
}

export async function adminUpdateUser(id: string, payload: AdminUpdateUserRequest): Promise<void> {
  await apiClient.patch(`/api/admin/users/${id}`, payload);
}

// ===== 任务管理 =====
export async function adminListTasks(params?: {
  page?: number;
  limit?: number;
  status?: string;
  needsAdminReview?: boolean;
}): Promise<{ data: Task[]; meta: PaginationMeta }> {
  const response = await apiClient.get("/api/admin/tasks", { params });
  return { data: response.data.data, meta: response.data.meta };
}

export async function adminResolveDispute(taskId: string, payload: AdminResolveDisputeRequest): Promise<void> {
  await apiClient.patch(`/api/admin/tasks/${taskId}/resolve`, payload);
}

// ===== 审核管理 =====
export async function adminListModerationRecords(params?: {
  page?: number;
  limit?: number;
  riskLevel?: ModerationResult;
  adminReviewStatus?: AdminReviewStatus;
}): Promise<{ data: ModerationRecord[]; meta: PaginationMeta }> {
  const response = await apiClient.get("/api/admin/moderation/records", { params });
  return { data: response.data.data, meta: response.data.meta };
}

export async function adminReviewModerationRecord(
  id: string,
  payload: AdminReviewModerationRequest,
): Promise<void> {
  await apiClient.patch(`/api/admin/moderation/records/${id}/review`, payload);
}

// ===== 系统配置 =====
export async function adminListConfigs(): Promise<ConfigItem[]> {
  const response = await apiClient.get("/api/admin/configs");
  return response.data.data;
}

export async function adminUpdateConfig(key: string, payload: AdminUpdateConfigRequest): Promise<void> {
  await apiClient.put(`/api/admin/configs/${key}`, payload);
}

// ===== 首页内容配置 =====
export async function adminListHomepageBlocks(): Promise<HomepageBlock[]> {
  const response = await apiClient.get("/api/admin/homepage/blocks");
  return response.data.data;
}

export async function adminUpdateHomepageBlock(id: string, payload: HomepageBlockUpsert): Promise<void> {
  await apiClient.put(`/api/admin/homepage/blocks/${id}`, payload);
}
