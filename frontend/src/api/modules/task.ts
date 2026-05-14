/**
 * 文件说明：
 * 这是任务模块的 API 封装占位文件。
 * A 同学后续应在这里集中维护任务大厅、详情、接单、提交完成、验收、争议等请求。
 */
import apiClient from "@/api/client";

export async function fetchTaskList() {
  const response = await apiClient.get("/api/tasks");
  return response.data;
}

