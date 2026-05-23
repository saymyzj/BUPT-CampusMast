import apiClient from "@/api/client";
import type {
  ChatConversation,
  ChatMessage,
  SendChatMessageRequest,
  MarkConversationReadRequest,
  PaginationMeta,
} from "@/types/api";

export async function listChatConversations(): Promise<ChatConversation[]> {
  const response = await apiClient.get("/api/chat/conversations");
  return response.data.data;
}

export async function listTaskChatMessages(
  taskId: string,
  params?: { page?: number; limit?: number },
): Promise<{ data: ChatMessage[]; meta: PaginationMeta }> {
  const response = await apiClient.get(`/api/chat/tasks/${taskId}/messages`, { params });
  return { data: response.data.data, meta: response.data.meta };
}

export async function createTaskChatMessage(
  taskId: string,
  payload: SendChatMessageRequest,
): Promise<ChatMessage> {
  const response = await apiClient.post(`/api/chat/tasks/${taskId}/messages`, payload);
  return response.data.data;
}

export async function markConversationRead(
  conversationId: string,
  payload: MarkConversationReadRequest,
): Promise<void> {
  await apiClient.patch(`/api/chat/conversations/${conversationId}/read`, payload);
}
