import apiClient from "@/api/client";
import type {
  Task,
  TaskDetail,
  TaskListParams,
  CreateTaskRequest,
  SubmitTaskProofRequest,
  RejectTaskRequest,
  RateTaskPartnerRequest,
  Rating,
  PaginationMeta,
} from "@/types/api";
import { isTaskVisible } from "@/utils/taskVisibility";

export async function createTask(payload: CreateTaskRequest): Promise<TaskDetail> {
  const response = await apiClient.post("/api/tasks", payload);
  return response.data.data;
}

export async function listTasks(params?: TaskListParams): Promise<{ data: Task[]; meta: PaginationMeta }> {
  const response = await apiClient.get("/api/tasks", { params });
  const data = response.data.data.filter(isTaskVisible);
  return { data, meta: response.data.meta };
}

export async function getTaskById(id: string): Promise<TaskDetail> {
  const response = await apiClient.get(`/api/tasks/${id}`);
  return response.data.data;
}

export async function acceptTask(id: string): Promise<TaskDetail> {
  const response = await apiClient.patch(`/api/tasks/${id}/accept`);
  return response.data.data;
}

export async function submitTaskProof(id: string, payload: SubmitTaskProofRequest): Promise<TaskDetail> {
  const response = await apiClient.patch(`/api/tasks/${id}/submit`, payload);
  return response.data.data;
}

export async function confirmTask(id: string): Promise<TaskDetail> {
  const response = await apiClient.patch(`/api/tasks/${id}/confirm`);
  return response.data.data;
}

export async function rejectTask(id: string, payload: RejectTaskRequest): Promise<TaskDetail> {
  const response = await apiClient.patch(`/api/tasks/${id}/reject`, payload);
  return response.data.data;
}

export async function cancelTask(id: string): Promise<TaskDetail> {
  const response = await apiClient.patch(`/api/tasks/${id}/cancel`);
  return response.data.data;
}

export async function abandonTask(id: string): Promise<TaskDetail> {
  const response = await apiClient.patch(`/api/tasks/${id}/abandon`);
  return response.data.data;
}

export async function listMyPostedTasks(params?: {
  page?: number;
  limit?: number;
  status?: string;
}): Promise<{ data: Task[]; meta: PaginationMeta }> {
  const response = await apiClient.get("/api/tasks/my/posted", { params });
  const data = response.data.data.filter(isTaskVisible);
  return { data, meta: response.data.meta };
}

export async function listMyAcceptedTasks(params?: {
  page?: number;
  limit?: number;
  status?: string;
}): Promise<{ data: Task[]; meta: PaginationMeta }> {
  const response = await apiClient.get("/api/tasks/my/accepted", { params });
  const data = response.data.data.filter(isTaskVisible);
  return { data, meta: response.data.meta };
}

export async function rateTaskPartner(taskId: string, payload: RateTaskPartnerRequest): Promise<Rating> {
  const response = await apiClient.post(`/api/tasks/${taskId}/rating`, payload);
  return response.data.data;
}
