/**
 * 文件说明：
 * 这是通知状态仓库。
 * 当前先预留未读数和通知列表状态，A 同学后续可以把 HTTP 拉取与 WebSocket 推送
 * 都接入这里，避免散落在多个页面里。
 */
import { defineStore } from "pinia";
import { listChatConversations } from "@/api/modules/chat";
import { listNotifications } from "@/api/modules/notification";

export const useNotificationStore = defineStore("notification", {
  state: () => ({
    chatUnreadCount: 0,
    notificationUnreadCount: 0,
    unreadCount: 0,
    items: [] as Array<Record<string, unknown>>,
    loadingUnread: false,
  }),
  getters: {
    totalUnreadCount: (state) => state.chatUnreadCount + state.notificationUnreadCount,
  },
  actions: {
    setUnreadCount(count: number) {
      this.unreadCount = count;
    },
    setChatUnreadCount(count: number) {
      this.chatUnreadCount = Math.max(0, count);
    },
    setNotificationUnreadCount(count: number) {
      this.notificationUnreadCount = Math.max(0, count);
      this.unreadCount = this.notificationUnreadCount;
    },
    setItems(items: Array<Record<string, unknown>>) {
      this.items = items;
    },
    async refreshUnreadCounts() {
      this.loadingUnread = true;
      try {
        const [conversations, notifications] = await Promise.all([
          listChatConversations(),
          listNotifications({ page: 1, limit: 1, unreadOnly: true }),
        ]);
        this.setChatUnreadCount(conversations.reduce((sum, item) => sum + item.unreadCount, 0));
        this.setNotificationUnreadCount(notifications.meta.unreadCount ?? notifications.meta.total);
      } catch {
        // Keep the existing badge value when one source is temporarily unavailable.
      } finally {
        this.loadingUnread = false;
      }
    },
  },
});

