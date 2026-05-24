import type { Task, TaskStatus } from "@/types/api";

const HIDDEN_STATUSES = new Set<TaskStatus>(["CANCELLED", "EXPIRED", "CLOSED_BY_ADMIN"]);

export function isTaskOverdue(task: Pick<Task, "status" | "deadline">): boolean {
  if (task.status !== "PENDING") return false;
  return new Date(task.deadline).getTime() <= Date.now();
}

export function isTaskVisible(task: Pick<Task, "status" | "deadline">): boolean {
  return !HIDDEN_STATUSES.has(task.status) && !isTaskOverdue(task);
}

